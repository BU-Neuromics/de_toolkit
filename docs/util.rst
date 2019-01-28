``util`` - Counts and Column Data File Utilities
================================================

.. contents::
    :local:

Functions for performing statistical set enrichment methods, e.g.
Gene Set Enrichment Analysis

``tidy``
--------

Subset both the counts columns and column data rows by intersection, returning
new outputs for both. Note the tidied column data is not output by default, and
the user must specify the -p argument to obtain it.

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

