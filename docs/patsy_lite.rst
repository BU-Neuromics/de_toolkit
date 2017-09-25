Patsy-lite
==========

Introduction
------------

Some of the important operations in detk, most notably the ``de`` module,
require the user specify a statistical model. The patsy_ python package is
designed to describe statistical models in just this way. However, the
syntax for describing patsy models is not very machine-readable, e.g.
a linear model relating a continuous quantity to a categorical variable
might look as follows::

  cont_var ~ C(cat_var, levels=['A','B','C'])

The resulting full design matrix would have columns named something like::

  cont_var ~ Intercept + C(cat_var, levels=['A','B','C'])[T.B] + C(cat_var, levels=['A','B','C'])[T.C]

This is at least a little bit yuck, and gets very yuck as the number of
variables in the model increases. A more convenient and programmatically
accessible way to express these models might be::

  cont_var ~ cat_var[A,B,C]

resulting in the full matrix::

  cont_var ~ Intercept + cat_var__B + cat_var__C

These variable names are much more amenable to programmatic use. Thus,
detk implements a 'patsy-lite' syntax that follows these conventions,
using the patsy library as the brain behind resolving full rank model
matrices given column data.

.. _patsy: https://patsy.readthedocs.io/en/latest/

Syntax
------

The patsy-lite syntax uses the column names from column data files passed
to detk utilities. The following table contains example column data that
will be useful in describing the patsy-lite syntax.

+------+------------+------------+---------+---------+
| cont | binary_str | binary_int | cat_str | cat_int |
+------+------------+------------+---------+---------+
| 0.13 |    case    |     1      |    A    |    1    |
| 0.97 |  control   |     0      |    B    |    2    |
| 0.22 |    case    |     1      |    A    |    1    |
| 0.76 |  control   |     0      |    C    |    3    |
| 0.69 |  control   |     0      |    C    |    3    |
| 0.08 |    case    |     1      |    A    |    1    |
| 0.17 |    case    |     1      |    B    |    2    |
| 0.53 |  control   |     0      |    C    |    3    |
+------+------------+------------+---------+---------+

Patsy-lite has four types of terms:

- *scalar*: variables that are to be considered purely numeric.
  Examples include continuous measures and ordinal variables, e.g.
  ``cont``, ``binary_int``, or ``cat_int``.
- *binary*: variables that are binary categories or encoded as strings in the
  table. These terms are written in a design spec like ``binary_str`` or, if a
  reference group is specified, ``binary_str[control]``. In this instance, the
  ``control`` value is reference group. Binary variables use a dummy encoding,
  such that only a single binary vector appears in the full model matrix.
- *multinomial*: categorical variables that have more than two levels. These
  terms are written in a design spec like ``cat_str`` or ``cat_str[A,B,C,D]``
  to specify the desired order of levels. The first value specified (or by
  alphabetical order if omitted) is assumed to be the reference group. Multinomial
  variables use a dummy encoding, such that there is a binary vector for all but
  one of the levels in the full model matrix.
- *patsy*: there is limited support for passing other patsy term types (e.g.
  factorial terms, ``binary_str:cat_str``). You can try to put in expressions
  that patsy knows how to understand, like ``np.log(cont)``, but you do so at
  your own risk and I'm going to pretend to not be responsible for what befalls
  you if you choose to do so.

Every model is expected to have a set of terms on the left hand side and a set
of terms on the right hand side separated by the ``~`` operator. In general,
there should be only a single term on the left hand side. I didn't write any
tests to see what would happen if there are more than one, so the usual
disclaimer applies.

Depending on what type of term a variable is, the output column name in the
full model matrix will follow one of three patterns:

- literal pass through - exactly the same as the column name
- categorical - ``<variable name>__<level>``
- patsy-specific terms - e.g. ``np.log(x)``

The double underscores in categorical variables should make it easy to recognize
which variable an output column refers to, and make down-stream programmatic
analysis easier.

Some mostly non-differential expression related examples, assuming the variable
names in these examples are found in the appropriate column data file::

  height ~ weight + age
  disease_status[control] ~ age_at_death + batch + counts
  gross_domestic_product ~ continent[NoAm] + population + election_year[no]

The full model matrix column names from these models might be something like::

  height ~ Intercept + weight + age
  disease_status__case ~ Intercept + age_at_death + batch__2 + batch__3 + counts
  gross_domestic_product ~ Intercept + continent__SoAm + continent__Asia +
      continent__Aust + continent__Euro + continent__SoPo + population +
      election_year__yes

The special ``counts`` term
---------------------------

For most of the detk tools that use formulas, the intent is to perform some kind
of differential expression where the feature counts are somewhere in the model.
Since the patsy-lite terms refer to the column names in the column data file,
the astute analyst might wonder how the counts term for each feature gets
integrated into the formula. detk has a special term for this case: ``counts``.
This term can and should be included as if it was a normal *scalar* variable in
the design spec.

The location of the ``counts`` variable is different depending on the DE method
being used. For Firth's logistic regression, the counts variable is expected to
be on the right hand side of the equation. For DESeq2, it is expected to be the
only term on the left hand side. detk goes to less than Olympic lengths to ensure
the design it gets has the ``counts`` variable in the place that it expects, but
it should be ok.
