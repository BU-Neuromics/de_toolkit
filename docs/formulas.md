# Design formulas

## Introduction

Some of the important operations in detk, most notably the
[`de` module](tools/de.md), require the user to specify a statistical model.
General-purpose formula libraries such as R's `model.matrix` and the Python
package [formulaic] describe statistical models in just this way, but their
syntax is not very machine-readable. A linear model relating a continuous
quantity to a categorical variable looks like:

```text
cont_var ~ C(cat_var, levels=['A','B','C'])
```

and the resulting design matrix has columns named something like:

```text
cont_var ~ Intercept + C(cat_var, levels=['A','B','C'])[T.B] + C(cat_var, levels=['A','B','C'])[T.C]
```

This is at least a little bit yuck, and gets very yuck as the number of
variables grows. detk therefore implements its own formula syntax, the
**detk formula syntax**, where the same model is written:

```text
cont_var ~ cat_var[A,B,C]
```

producing the full matrix:

```text
cont_var ~ Intercept + cat_var__B + cat_var__C
```

These column names are much more amenable to programmatic use. detk
translates the formula for formulaic, which resolves the full-rank model
matrix from the column data.

[formulaic]: https://matthewwardrop.github.io/formulaic/

## Syntax

Formula terms refer to column names of the
[column data file](concepts.md#the-column-data-file). The examples below use
this column data:

| cont | binary_str | binary_int | cat_str | cat_int | flag  |
|------|------------|------------|---------|---------|-------|
| 0.13 | case       | 1          | A       | 1       | TRUE  |
| 0.97 | control    | 0          | B       | 2       | FALSE |
| 0.22 | case       | 1          | A       | 1       | TRUE  |
| 0.76 | control    | 0          | C       | 3       | FALSE |
| 0.69 | control    | 0          | C       | 3       | TRUE  |
| 0.08 | case       | 1          | A       | 1       | FALSE |
| 0.17 | case       | 1          | B       | 2       | TRUE  |
| 0.53 | control    | 0          | C       | 3       | FALSE |

There are four types of terms:

- **scalar** — variables treated as purely numeric: continuous measures and
  ordinal variables, e.g. `cont`, `binary_int`, or `cat_int`.
- **binary** — two-level categories encoded as strings, written `binary_str`
  or, with an explicit reference group, `binary_str[control]`. Binary
  variables use a dummy encoding: a single binary vector in the full model
  matrix. A column of `TRUE`/`FALSE` values is binary too: `flag` gives
  `flag__True`, with `FALSE` the reference, and `flag[TRUE]` gives
  `flag__False`.
- **multinomial** — categorical variables with more than two levels, written
  `cat_str` or `cat_str[A,B,C,D]` to specify the level order. The first level
  (or alphabetically first if omitted) is the reference group. Dummy encoding
  produces one binary vector per non-reference level.
- **interactions** — `binary_str:cat_str` is the interaction of two terms,
  and `binary_str*cat_str` is short for
  `binary_str + cat_str + binary_str:cat_str`. Either side of `:` or `*` may
  be any term above, with a reference or level list
  (`binary_str[control]:cat_str`).

Formulas take column names only. A term that is not a column and looks like
a function call, such as `np.log(cont)` or `log2(cont)`, is an error: a
derived column, such as a log-transformed covariate, belongs in the column
data file, where the formula can name it. A column whose name really is such
a string, say `log2(cont)`, is still a column.

Every model has a left hand side and a right hand side separated by `~`. In
general there should be a single term on the left hand side.

Output column names in the full model matrix follow three patterns:

- literal pass-through — exactly the column name (scalar terms)
- categorical — `<variable name>__<level>`
- interaction — the columns of each term joined by `:`, e.g.
  `binary_str__control:cat_str__B`

The double underscore makes it easy to recognize which variable an output
column refers to, and makes downstream programmatic analysis easier.

The columns come in a fixed order: the `Intercept`, then the columns of the
single terms in the order they are written, then the interactions. For
example, `cont ~ binary_str*cat_str` gives:

```text
cont ~ Intercept + binary_str__control + cat_str__B + cat_str__C +
    binary_str__control:cat_str__B + binary_str__control:cat_str__C
```

An interaction written alone is coded full rank, which brings in main-effect
columns of one of its terms. `cont ~
binary_str:cat_str` gives:

```text
cont ~ Intercept + cat_str__B + cat_str__C + binary_str__control:cat_str__A +
    binary_str__control:cat_str__B + binary_str__control:cat_str__C
```

Some mostly non-differential-expression examples:

```text
height ~ weight + age
disease_status[control] ~ age_at_death + batch[1] + counts
gross_domestic_product ~ continent[NoAm] + population + election_year[no]
```

giving full model matrix columns like the ones below. `batch` holds the
integers 1, 2 and 3, so `batch` alone would be a scalar term; `batch[1]` makes
it categorical with 1 the reference. The levels of a category without a level
list come in sorted order.

```text
height ~ Intercept + weight + age
disease_status__case ~ Intercept + age_at_death + batch__2 + batch__3 + counts
gross_domestic_product ~ Intercept + continent__Asia + continent__Aust +
    continent__Euro + continent__SoAm + continent__SoPo + population +
    election_year__yes
```

## The special `counts` term

For detk tools that fit a model per feature, the feature counts must appear
somewhere in the model. Since formula terms refer to column data columns, detk
provides the special term **`counts`** for this purpose; include it as if it
were a normal scalar variable.

Where `counts` goes depends on the DE method:

- **DESeq2**: `counts` must be the *only* term on the left hand side —
  `counts ~ AgeOfDeath + Status`
- **Firth logistic regression**: `counts` goes on the *right* hand side, with
  the sample class on the left — `Status ~ AgeOfDeath + counts`

detk checks that the design has `counts` where the method expects it.
