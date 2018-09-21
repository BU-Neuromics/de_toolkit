``outlier`` - Outlier Identification
====================================

.. contents::
    :local:

Functions for identifying/manipulating outlier counts.

``entropy``
-----------
.. autofunction:: de_toolkit.outlier.entropy

Command line usage::

    Usage:
        detk-outlier entropy <counts_fn> [options]

    Options:
        -p P --percentile=P    Float value between 0 and 1
        -o FILE --output=FILE  Name of the ouput csv
        --plot-output=FILE     Name of the plot png

``shrink``
----------
.. autofunction:: de_toolkit.outlier.shrink

Command line usage::

    Usage:
        detk-transform shrink [options] <count_fn>

    Options:
        -o FILE --output=FILE  Destination of primary output [default: stdout]

