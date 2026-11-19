---
template: adr
state: Accepted
authority: [human]
date: 2026-11-18
from: {node: release}
applies: [release/formula-migrate]
revisions:
  - {date: 2026-11-18, by: adamlabadorf, change: Study of the formulaic migration and the statsmodels questions written in; Option B is now keeping patsy for 1.0; title widened, why: "Adam asked for an estimate before deciding, and for formulaic to be compared with keeping patsy (2026-11-18)"}
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: option A, formulaic; rename patsy_lite.py (name in DETK-0027)"}
---

# The formula library behind patsy-lite for 1.0

- Proposed by: the planning session for DETK-0001 Option B, 2026-11-18.
  Adam is leaning toward formulaic but has not decided. He asked for an
  estimate of the migration first, then asked (since statsmodels still
  depends on patsy) for formulaic to be compared with keeping patsy.

## Background

Adam chose Option B of DETK-0001 (#18): replace docopt-ng and patsy
before 1.0 is tagged. On the parser he then chose argparse (DETK-0023).
On formulas he said: "Let's use argparse and formulaic, though I'd like to
see how much work the migration from patsy to formulaic will be before
formally deciding."

detk's design formulas (`docs/formulas.md`) use a syntax called
"patsy-lite". `de_toolkit/patsy_lite.py` reads a formula with ply and
rewrites `cat[A,B,C]` and `cat[ref]` as patsy terms (`C(...)`,
`Treatment(...)`, `Q("...")` for awkward names). patsy then builds the
full-rank model matrix, and detk renames its columns to
`variable__level`. This record holds the study of what replacing patsy
would take, so Adam can decide.

## Context

### Where detk uses patsy

- `de_toolkit/patsy_lite.py` is the only module that imports patsy:
  `from patsy import ModelDesc, dmatrices, PatsyError` (line 3).
  `patsy_lite_to_patsy` builds a `ModelDesc` (line 121) and
  `DesignMatrix.__init__` calls `dmatrices` (line 154). It also uses
  `ModelDesc.rhs_termlist` and `term.name()` to undo patsy's reordering
  of terms.
- `DesignMatrix` is used through `CountMatrix` (`common.py`, lines
  25 and 226), and by `de.py` (DESeq2 and Firth), `norm.py` (deseq2) and
  `transform.py` (vst, rlog). Those use only detk's own API: `.design`,
  `.lhs`, `.rhs`, `.full_matrix`, `drop_from_lhs`/`drop_from_rhs`.
  None of them touches patsy.
- What users see: the renamed design string goes into the module JSON
  and provenance params (`"design": count_obj.design`). The column names
  go into the metadata table handed to R. DESeq2 result columns are named
  `<design column>__<statistic>` (`de.py`, the R script's
  `paste(name, colnames(res.df), sep='__')`). So the column names are
  part of the 1.0 promise.

### Does detk hand formulas to statsmodels?

No. Nothing in `de_toolkit/` imports statsmodels. A search for
`statsmodels`, `from_formula`, `formula.api` and `smf` across the package
finds nothing, and no other module uses `importlib`/`__import__` to load
it. The only use is a test, `tests/de/test_de.py` lines 310-336, which
compares Firth with ordinary logistic regression. That test passes a
design matrix built by detk to `sm.Logit(endog, exog)`, the array API,
with no formula. statsmodels is still a runtime dependency in
`pyproject.toml` (`statsmodels>=0.14`, locked at 0.14.6) and in
`environment.yml`, but the package code does not use it. It appears to
be left over from older code.

So if detk switched, there would be no second formula engine inside
detk: statsmodels never parses a detk formula, and detk's column names,
reference levels, contrasts and NA handling all come from patsy-lite. A
user would see the two engines disagree only by fitting their own
statsmodels formula on detk's column data next to a detk run. That is
outside detk, and Adam chose not to promise the Python API.

### What statsmodels is doing about formulaic (checked 2026-11-18)

- statsmodels 0.15.0, released 2026-08-27, added formulaic as a second
  formula engine. Its release notes have the heading "Formula engine:
  patsy is no longer the only option". They say patsy is "the default
  engine when it is installed, for backward compatibility", and that "The
  engine can be selected explicitly with the `SM_FORMULA_ENGINE`
  environment variable (`"patsy"` or `"formulaic"`)". They also say this
  "lays the groundwork for statsmodels to move away from `patsy`, which
  has been in low-maintenance mode for several years". No removal date
  is given.
  Source: <https://www.statsmodels.org/stable/release/index.html> (public),
  also <https://github.com/statsmodels/statsmodels/releases> (public).
- Under 0.15.0, formulaic is a required runtime dependency even when
  patsy is the engine. PyPI's metadata for 0.15.0 lists both
  `patsy>=0.5.6` and `formulaic>=1.1.0`.
  Source: <https://pypi.org/pypi/statsmodels/json> (public).
- So once detk's lock moves to statsmodels 0.15, both patsy and formulaic
  are installed whichever one patsy-lite uses, while statsmodels stays a
  detk dependency. Today's lock (0.14.6) installs patsy only.

### The study: patsy-lite on formulaic (2026-11-18)

Run in a throwaway environment outside the repository (formulaic 1.2.2,
patsy 1.0.3, pandas 3.1.1, Python 3.13). The project's code and
dependencies were not changed.

- **Method.** Two copies of `patsy_lite.py` were run on the same data
  frames: the current one, and a minimal port. The port changed four
  things: it built a `formulaic.Formula` and called
  `formulaic.model_matrix`, quoted awkward names with backticks instead
  of `Q("...")`, mapped formulaic's intercept term `1` to the `Intercept`
  column when restoring term order, and cast the matrices to float. Both
  copies were given every formula in `tests/patsy_lite`, `tests/de`,
  `tests/common` and `docs/formulas.md` (26 formulas plus 4 invalid
  ones). For each, the `.design` strings were compared and, where those
  matched, the matrix values.
- **Result.** 21 of the 26 gave identical design strings and identical
  matrix values. That covered every term type in `docs/formulas.md`:
  scalar, binary and multinomial with and without a reference or level
  order, integer-coded categories (`batch[2]`), `counts` on either side,
  `-1`, `~ 1`, the interactions `a:b` and `a*b`, and names with dots
  (`fld.cat_int[4,1,2,3]`).
- **Differences found:**
  1. *Boolean columns.* patsy treats a bool column as categorical
     (`binary_bool__True`); formulaic treats it as numeric
     (`binary_bool`). detk's table reader lets pandas infer column types,
     so a column data file with `TRUE`/`FALSE` gives a bool column. Users
     would see a different design string and different DESeq2/Firth
     result column names unless the port converts bool columns to
     categorical first. The study tried that conversion and it restored
     patsy's names (`b[T.True]`). Small fix; needs a pin test.
  2. *Matrix dtype.* formulaic's dummy columns are int64; patsy's are
     float64. Casting to float keeps the matrices identical; without the
     cast, the metadata CSV handed to R would read `1` where it now reads
     `1.0`.
  3. *Quoting.* patsy-lite's name map is keyed on `Q("name")`. formulaic
     names that column `Q('name')`, so the map has to switch to
     backticks, which formulaic supports. Done in the port; no visible
     change.
  4. *Error messages.* Invalid designs (unknown column, unknown level)
     still raise `PatsyLiteParseError` with the same "Misspecified
     column" prefix, but the wrapped text comes from formulaic
     ("Unable to evaluate factor ..." instead of "Error evaluating
     factor ..."). No test asserts on that text. A formula with no left
     side (`~ x`) fails under both engines, but in the port it fails
     with an unwrapped `AttributeError`. The real port should keep
     raising `PatsyLiteParseError`.
  5. *Term order.* Both engines sort terms by degree. patsy-lite's
     reordering step has to read term names from formulaic's `Formula`
     instead of patsy's `ModelDesc`. Done in the port, with the same
     result.
- **Same under both engines:** NA handling (rows with a missing value
  are dropped, 6 of 8 rows in the probe), the alphabetical default
  reference level, explicit `levels=` order, `Treatment(ref)` reference
  levels (formulaic accepts patsy's `Treatment` spelling), full-rank
  coding of a categorical left side with an intercept, and the `T.`
  column naming that the `__` renaming relies on.
- **Broken today under either engine:** `docs/formulas.md` says other
  patsy terms such as `np.log(cont)` pass through "at your own risk".
  They do not work today: `quote_var` quotes any name containing `.` or
  `(`, so `np.log(x)` is looked up as a column named `np.log(x)` and
  fails. The existing tests only check the translation string, which
  hides this. The formulaic port fails the same way. This is a
  documentation or feature question, separate from the choice of
  library.

### Size of the formulaic migration

**Small.** In `patsy_lite.py`, about 30-40 lines change: the import,
building the formula object (about 10 lines), quoting, term reordering,
the bool conversion, the float cast, and error wrapping, including
formulas with no left side. No caller changes: `common.py`, `de.py`,
`norm.py` and `transform.py` use only `DesignMatrix`'s own API. Tests:
`test_patsy_lite_to_patsy` asserts patsy's `ModelDesc.describe()`
strings (about 12 asserts), so it is rewritten against whatever the
translation returns. The `DesignMatrix` tests should pass unchanged, and
`release/formula-pin` adds fixtures for bool columns, dtype and the
error cases. `docs/formulas.md` changes in a few paragraphs, and the
`np.log` claim has to be fixed or made true either way. The reason it is
small: the formula language and the column naming match, so detk's
`__` layer barely changes. The main risk is the R-gated DE outputs, and
identical matrices make that low.

## Options

The criteria: the same matrices and column names for the documented
syntax (the 1.0 promise); maintenance after 1.0; what is installed; the
cost before the tag.

### Option A: formulaic

- Cost: small (above). One new direct dependency, which statsmodels
  0.15 installs anyway.
- Risk: low and known. Bool columns and dtype need handling in the port,
  and the pin tests catch both. Error message text changes.
- For 1.0: detk's formula backend is the library statsmodels says it is
  moving toward. The documented syntax and column names are unchanged if
  the pin tests pass. patsy stays installed through statsmodels until
  statsmodels drops it, or until detk drops statsmodels.

### Option B: keep patsy for 1.0

- Cost: none before the tag, apart from `release/formula-pin` (worth
  doing either way) and the `np.log` docs fix. `release/formula-migrate`
  would be dropped or moved after 1.0.
- Risk: none now. Later, patsy is in "low-maintenance mode" by
  statsmodels' account, so a migration after 1.0 would happen under the
  semver promise. The pin tests would make that migration just as safe
  then, and nothing in the study suggests it would cost more.
- For 1.0: the design-matrix behaviour users rely on is unchanged by
  construction. This departs from the formula half of DETK-0001 Option B
  ("switching to better supported libraries before the release"), so
  DETK-0001's Decision would need revising.

### Option C: no formula library

Build the model matrix in detk with pandas from the parsed patsy-lite
terms. No dependency, but detk has to implement interactions (`a:b`,
`a*b`, which work today) and full-rank coding itself. That is more code
than A for no change users would see. Listed for completeness.

### A related dependency question (not decided here)

statsmodels is a runtime dependency that detk's package code does not
use. Moving it to the test extra would take patsy, and under 0.15
formulaic, off users' installs unless patsy-lite needs them. That is a
dependency and promise question for Adam. It is outside this record and
outside `release/formula-migrate`'s scope.

## Decision

Option A, formulaic, chosen by Adam on 2026-11-19 (relayed by the driver
session): "0024 - accept the migration to formulaic and proceed to
planning and implementation, and we need to rename patsy_lite.py to
something else." The port carries the study's fixes: bool columns are
made categorical and the matrices are cast to float, so the design
strings and column names stay as they are. The new module name is
DETK-0027. Whether formulas keep transforms such as `np.log(x)` is
DETK-0028. Both are Adam's.

## Consequences

Under A, `release/formula-migrate` carries out the port as studied and
`release/formula-pin` adds the bool, dtype and error-case fixtures. Under
B, `release/formula-migrate` is abandoned or moved to `features`,
DETK-0001's Decision is revised to drop the formula half, and
`release/formula-pin` still lands. Under either, the `np.log`
pass-through in `docs/formulas.md` is fixed or removed.

## How to reproduce

In a fresh virtual environment (not the project's): `uv venv` and
`uv pip install formulaic patsy pandas numpy ply`. Copy
`de_toolkit/patsy_lite.py` twice and apply the four changes from the
method above to one copy. Build `DesignMatrix` from both copies over a
random data frame with the columns `cont`, `binary_str`, `binary_int`,
`cat_str`, `cat_int`, `binary_bool`, `x`, `a`, `b`, `counts`, `batch`
(and the same columns with an `fld.` prefix). Compare `.design` and
`.full_matrix.values`. The formula list is the set quoted in
`tests/patsy_lite`, `tests/de`, `tests/common` and `docs/formulas.md`.
