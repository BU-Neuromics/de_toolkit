# Design formulas

## Introduction

Some of the important operations in detk, most notably the
[`de` module](tools/de.md), require the user to specify a statistical model.
The [patsy] Python package describes statistical models in just this way, but
its syntax is not very machine-readable. A linear model relating a continuous
quantity to a categorical variable looks like:

```text
cont_var ~ C(cat_var, levels=['A','B','C'])
```

and the resulting design matrix has columns named something like:

```text
cont_var ~ Intercept + C(cat_var, levels=['A','B','C'])[T.B] + C(cat_var, levels=['A','B','C'])[T.C]
```

This is at least a little bit yuck, and gets very yuck as the number of
variables grows. detk therefore implements a "patsy-lite" formula syntax where
the same model is written:

```text
cont_var ~ cat_var[A,B,C]
```

producing the full matrix:

```text
cont_var ~ Intercept + cat_var__B + cat_var__C
```

These column names are much more amenable to programmatic use. patsy remains
the brain behind resolving full-rank model matrices from column data.

[patsy]: https://patsy.readthedocs.io/en/latest/

## Syntax

Formula terms refer to column names of the
[column data file](concepts.md#the-column-data-file). The examples below use
this column data:

| cont | binary_str | binary_int | cat_str | cat_int |
|------|------------|------------|---------|---------|
| 0.13 | case       | 1          | A       | 1       |
| 0.97 | control    | 0          | B       | 2       |
| 0.22 | case       | 1          | A       | 1       |
| 0.76 | control    | 0          | C       | 3       |
| 0.69 | control    | 0          | C       | 3       |
| 0.08 | case       | 1          | A       | 1       |
| 0.17 | case       | 1          | B       | 2       |
| 0.53 | control    | 0          | C       | 3       |

There are four types of terms:

- **scalar** — variables treated as purely numeric: continuous measures and
  ordinal variables, e.g. `cont`, `binary_int`, or `cat_int`.
- **binary** — two-level categories encoded as strings, written `binary_str`
  or, with an explicit reference group, `binary_str[control]`. Binary
  variables use a dummy encoding: a single binary vector in the full model
  matrix.
- **multinomial** — categorical variables with more than two levels, written
  `cat_str` or `cat_str[A,B,C,D]` to specify the level order. The first level
  (or alphabetically first if omitted) is the reference group. Dummy encoding
  produces one binary vector per non-reference level.
- **patsy** — limited support for passing other patsy term types (e.g.
  interaction terms `binary_str:cat_str`, or expressions like `np.log(cont)`).
  You do so at your own risk.

Every model has a left hand side and a right hand side separated by `~`. In
general there should be a single term on the left hand side.

Output column names in the full model matrix follow three patterns:

- literal pass-through — exactly the column name (scalar terms)
- categorical — `<variable name>__<level>`
- patsy-specific — e.g. `np.log(x)`

The double underscore makes it easy to recognize which variable an output
column refers to, and makes downstream programmatic analysis easier.

Some mostly non-differential-expression examples:

```text
height ~ weight + age
disease_status[control] ~ age_at_death + batch + counts
gross_domestic_product ~ continent[NoAm] + population + election_year[no]
```

giving full model matrix columns like:

```text
height ~ Intercept + weight + age
disease_status__case ~ Intercept + age_at_death + batch__2 + batch__3 + counts
gross_domestic_product ~ Intercept + continent__SoAm + continent__Asia +
    continent__Aust + continent__Euro + continent__SoPo + population +
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
