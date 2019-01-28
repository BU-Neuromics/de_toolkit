``util`` - Counts and Column Data File Utilities
================================================

.. contents::
    :local:

Functions for tidying up counts and column data files. Mostly this means
subsetting one or the other so that the column IDs and order match.
Combined with ``csvgrep`` from the csvkit_ package, this is useful for
extracting subsets of samples for downstream differential expression
analysis.

.. _csvkit: https://csvkit.readthedocs.io

``tidy``
--------

Subset both the counts columns and column data rows by intersection, returning
new outputs for both. Note the tidied column data is not output by default, and
the user must specify the ``-p`` argument to obtain it.

Command line usage::

    Usage:
        detk-util tidy [options] <count_fn> <cov_fn>

    Options:
        -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
        -p FILE --column-data-output=FILE  Destination of tidied column data


``tidy-counts``
---------------

Subset and order the provided counts file columns according to the rows of the
provided column data file. Operation will fail if there are rows in the column
data file that do not exist as columns in the counts file.

Command line usage::

    Usage:
        detk-util tidy-counts [options] <count_fn> <cov_fn>

    Options:
        -o FILE --output=FILE  Destination of tidied counts data [default: stdout]


``tidy-covs``
-------------

Subset and order the provided column data file rows according to the columns of
the provided ccounts data file. Operation will fail if there are columns in the
counts file that do not exist as rows in the column data file.

Command line usage::

    Usage:
        detk-util tidy-covs [options] <count_fn> <cov_fn>

    Options:
        -o FILE --output=FILE  Destination of tidied column data [default: stdout]

