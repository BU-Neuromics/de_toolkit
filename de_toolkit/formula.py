from dataclasses import dataclass, field
import logging
import re
import warnings

import formulaic
from formulaic.errors import DataMismatchWarning
import pandas
from ply import lex

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class FormulaParseError(Exception):
    pass


tokens = ("CONSTANT", "FACTORTERM", "RELATION", "OP", "COUNT")

t_COUNT = r"count"
t_CONSTANT = r"-?\d+(?:\.\d*)?"
t_RELATION = r"~"
# : joins the terms of an interaction, so a:b and a[ref]:b are two terms
t_OP = r"[-+*/:]"
t_ignore = " "


def t_FACTORTERM(t):
    r"([\w](?:[\w.()]+)?)(?:\[([^]]+)\])?"
    # this regex returns a bunch of empty groups for some reason
    # filter out the None valued groups and just operate on what
    # is left
    groups = [_ for _ in t.lexer.lexmatch.groups() if _][1:]
    if len(groups) == 1:
        t.term = groups[0]
    elif len(groups) == 2:
        args = groups[1]
        if "," in args:
            t.term, t.levels = groups[0], args
            t.levels = t.levels.split(",")
        else:
            t.term, t.ref = groups[0], args
    return t


# a term that looks like a call, np.log(x) or log2(x): a name, then (...)
CALL = re.compile(r"[A-Za-z_][\w.]*\(.*\)")


def check_calls(model, columns):
    """
    Raise FormulaParseError for a term of *model* that is not one of
    *columns* and looks like a call: formulas take column names only
    (DETK-0050). A column whose name looks like a call is still a column.
    """
    for term in model.name_map.values():
        if term not in columns and CALL.fullmatch(term):
            raise FormulaParseError(
                f"Formulas take column names only: {term} is not a column of the "
                "column data file and looks like a call. Add the derived column to "
                "the column data file and name it in the formula."
            )


def t_error(t):
    return t


lexer = lex.lex()


def quote_var(v):
    "Quote a column name formulaic would not read as a name, with backticks."
    if any(_ in v for _ in "#.()[]@"):
        return f"`{v}`"
    return v


# R's reserved words (?Reserved); make.names() alters all but ... and ..1, ..2
R_RESERVED = frozenset(
    "if else repeat while function for next break in TRUE FALSE NULL Inf NaN NA "
    "NA_integer_ NA_real_ NA_character_ NA_complex_ ...".split()
)
# a syntactic R name, as make.names() leaves it: a letter, or a dot not
# followed by a digit, then letters, digits, dots and underscores. Only ASCII
# letters count, since R's letters depend on the locale; quoting a name R
# would also read plainly is harmless.
R_SYNTACTIC = re.compile(r"(?:[A-Za-z]|\.(?![0-9]))[A-Za-z0-9._]*|\.")
# the only numeral detk writes in a resolved design: the 1 of a trivial
# model, counts ~ 1 (DesignMatrix.design). Any other number-shaped term,
# such as 2.5 or 1.0, is a column name (the parser takes decimals as
# columns) and is quoted, or R would read it as a constant.
R_INTERCEPT = "1"


def r_name(name):
    """
    *name* as R reads it as a name: backtick-quoted, with backticks and
    backslashes in it escaped, unless it is a syntactic R name that is not a
    reserved word (or ..1, ..2, ...).
    """
    if (
        R_SYNTACTIC.fullmatch(name)
        and name not in R_RESERVED
        and not re.fullmatch(r"\.\.\d+", name)
    ):
        return name
    escaped = name.replace("\\", "\\\\").replace("`", "\\`")
    return f"`{escaped}`"


def r_design(design):
    """
    The R-bound form of the resolved *design* (``CountMatrix.design``, as
    ``lhs ~ rhs`` with terms joined by `` + ``): every name in it that R
    would not read as a plain name is backtick-quoted, so R's ``formula()``
    reads each as a column name and runs none as code (DETK-0050). An
    interaction ``a:b`` stays an interaction of the names ``a`` and ``b``.
    Only the intercept ``1`` of ``counts ~ 1`` is left bare: a number-shaped
    column name such as ``2.5`` is quoted like any other.
    The resolved design itself, unquoted, is what detk records.
    """
    if "~" not in design:
        raise FormulaParseError(f"The design {design!r} has no ~")
    lhs, rhs = design.split("~", 1)

    def side(s):
        terms = [_.strip() for _ in s.split(" + ")]
        return " + ".join(
            term if term == R_INTERCEPT else ":".join(r_name(_) for _ in term.split(":"))
            for term in terms
            if term
        )

    lhs, rhs = side(lhs), side(rhs)
    return f"{lhs} ~ {rhs}" if lhs else f"~ {rhs}"


def repr_val(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        pass
    try:
        return float(v)
    except (ValueError, TypeError):
        pass
    return v


def is_bool_column(col):
    "True if *col* holds booleans (bool dtype, or bools with missing values)."
    if pandas.api.types.is_bool_dtype(col):
        return True
    if col.dtype == object:
        values = col.dropna()
        return len(values) > 0 and all(isinstance(_, bool) for _ in values)
    return False


def bool_level(level):
    "A level written for a boolean column (TRUE, False, true, ...) as a bool."
    if isinstance(level, str) and level.lower() in ("true", "false"):
        return level.lower() == "true"
    return level


@dataclass
class TranslatedFormula:
    """
    A detk formula translated to formulaic's syntax.

    *formula* is the formulaic formula string. *name_map* maps each term as
    written in it to the column name it stands for, and is used to give
    the model matrix columns their detk formula names. *levels* maps a
    column given a level list to that list.
    """

    formula: str
    name_map: dict = field(default_factory=dict)
    levels: dict = field(default_factory=dict)

    def describe(self):
        return self.formula


def to_formulaic(formula, bool_columns=()):
    """
    Translate the detk *formula* to formulaic's syntax.

    The levels written for a column named in *bool_columns* are read as
    booleans, in any case (TRUE, False, ...).
    """

    # I guess we assume there is always a lhs and a rhs?
    if "~" not in formula:
        raise FormulaParseError(
            "A ~ must be specified, so that there is a left and right hand side"
        )

    lexer.input(formula)

    translated = []
    # the name map is used later to replace formulaic's column names with
    # the column names as written in the formula
    name_map = {}
    levels = {}

    while True:
        try:
            tok = lexer.token()
        except lex.LexError as e:
            raise FormulaParseError(f"Error parsing formula:\n{formula}\n{e.args}") from e

        if not tok:
            break

        if tok.type in ("CONSTANT", "RELATION", "OP", "COUNT"):
            translated.append(tok.value)

        # term
        # term[ref] -> C(term, Treatment("ref"))
        # term[lev1,lev2,lev3] -> C(term, levels=["lev1","lev2","lev3"])
        if tok.type == "FACTORTERM":
            to_val = repr_val
            if tok.term in bool_columns:

                def to_val(v):
                    return bool_level(repr_val(v))

            if hasattr(tok, "ref"):
                term = f"C({quote_var(tok.term)}, Treatment({to_val(tok.ref)!r}))"
                name_map[term] = tok.term
            elif hasattr(tok, "levels"):
                term_levels = [to_val(_) for _ in tok.levels]
                term = f"C({quote_var(tok.term)}, levels={term_levels})"
                name_map[term] = tok.term
                levels[tok.term] = term_levels
            else:
                term = quote_var(tok.value)
                name_map[term] = tok.value
            translated.append(term)

    return TranslatedFormula(" ".join(translated), name_map, levels)


class ModelError(Exception):
    pass


class DesignMatrix:
    def __init__(self, formula, model_data):

        self._formula = formula
        logger.debug("DesignMatrix formula: %s", formula)
        self._model_data = model_data

        # when there is a categorical veriable on the lhs, the vector
        # space of all levels is included where, for example, we're only
        # interested in the vector space of the reference level for
        # logistic regression (i.e., one column with zero for reference
        # samples and one for the other)
        # we can control this by adding an intercept to the lhs, which
        # will acheive the desired result and has no effect when
        # including, e.g. continuous variables
        # we remove the Intercept term from the lhs before returning
        # the design matrix
        if not formula.strip().startswith("~"):
            formula = f"1 + {formula}"

        # formulaic treats a bool column as numeric; make it categorical,
        # so a TRUE/FALSE column gives flag__True with False the reference
        data = model_data.copy()
        bool_columns = [c for c in data.columns if is_bool_column(data[c])]
        for c in bool_columns:
            data[c] = pandas.Categorical(data[c], categories=[False, True])

        model = to_formulaic(formula, bool_columns)
        logger.debug("translated formulaic formula: %s", model.describe())
        check_calls(model, data.columns)

        # formulaic turns a value outside a level list into a missing value
        # and drops its sample with a warning; report it as an error instead
        for column, column_levels in model.levels.items():
            if column in data:
                unlisted = sorted(set(data[column].dropna()) - set(column_levels), key=str)
                if unlisted:
                    raise FormulaParseError(
                        f"Misspecified column in design, check term names. "
                        f"{column} has the level(s) {', '.join(map(repr, unlisted))}, "
                        f"which are not among the levels given: {column_levels}"
                    )

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", DataMismatchWarning)
                matrices = formulaic.model_matrix(model.describe(), data)
        except Exception as e:
            raise FormulaParseError(
                f"Misspecified column in design, check term names. {e.args}"
            ) from e

        if not hasattr(matrices, "lhs"):
            raise FormulaParseError(
                f"The design {self._formula!r} has no left hand side: name the outcome "
                "(counts, or the column to model) before the ~"
            )

        # columns come in formulaic's order (DETK-0049): the intercept, then
        # terms by degree, each degree in the order written
        self.lhs = pandas.DataFrame(matrices.lhs).astype("float64")
        self.rhs = pandas.DataFrame(matrices.rhs).astype("float64")

        # formulaic's column names are ugly and not very machine (or
        # human) readable; replace them with the detk formula names
        def rename_model_cols(c):
            for k, v in model.name_map.items():
                if k in c:
                    c = c.replace(k, v)
            # categorical variables look like
            # C(term, Treatment('cont'))[T.case] or term[A] in an interaction
            # replace [T.case] -> __case
            cat_match = r"\[(?:T\.)?(\w*)\]"
            if re.search(cat_match, c):
                c = re.sub(cat_match, r"__\1", c)
            return c

        self.lhs.rename(columns=rename_model_cols, inplace=True)
        self.rhs.rename(columns=rename_model_cols, inplace=True)

        # remove the Intercept term from the lhs that we added at the beginning
        self.drop_from_lhs("Intercept")

        logger.debug("final design: %s", self.design)

    @property
    def design(self):
        lhs = " + ".join(self.lhs.columns)
        rhs = " + ".join(self.rhs.columns)
        # it is sometimes useful to have a trivial model, e.g. counts ~ 1
        if len(rhs) == 0:
            rhs = "1"
        return " ".join([lhs, "~", rhs])

    def drop_from_lhs(self, column, quiet=False):
        try:
            self.lhs.drop(column, axis=1, inplace=True)
        except KeyError as e:
            if not quiet:
                raise ModelError(f"Cannot drop {column} from lhs, does not exist") from e

    def drop_from_rhs(self, column, quiet=False):
        try:
            self.rhs.drop(column, axis=1, inplace=True)
        except KeyError as e:
            if not quiet:
                raise ModelError(f"Cannot drop {column} from rhs, does not exist") from e

    def head(self):
        return self.full_matrix.head()

    @property
    def full_matrix(self):
        return pandas.concat([self.lhs, self.rhs], axis=1)

    def augment(self, df, side):
        """Return a new DesignMatrix with the columns (or keys) of *df* appended to
        the left or right hand side

        """
        if side == "lhs":
            new_design = "{} + {}".format("+".join(df.columns), self._formula)
        else:
            new_design = "{} + {}".format(self._formula, "+".join(df.columns))
        model_data = pandas.concat([self._model_data, df], axis=1)
        return DesignMatrix(new_design, model_data)

    def augment_lhs(self, df):
        """Return a new DesignMatrix with the columns (or keys) of *df* appended to
        the left hand side

        """
        return self.augment(df, "lhs")

    def augment_rhs(self, df):
        """Return a new DesignMatrix with the columns (or keys) of *df* appended to
        the right hand side

        """
        return self.augment(df, "rhs")

    def update_design(self, column, values):
        """Update the DesignMatrix *column* with *values*"""
        if column in self.lhs:
            self.lhs[column] = values
        elif column in self.rhs:
            self.rhs[column] = values
        else:
            raise ModelError(f"Cannot replace values for column {column}, column does not exist")
