``stats`` - Count Matrix Statistics
===================================

.. contents::
    :local:

Easy access to informative count matrix statistics. Each of these functions
produces three outputs:

- a tabular form of the statistics, formatted either as CSV or a human
  readable table using the terminaltables_ package
- a json_ formatted file containing relevant statistics in a machine-parsable
  format
- a human-friendly HTML page displaying the results

All of the commands accept a single counts file as input with optional
arguments as indicated in the documentation of each subtool. By default, the
JSON and HTML output files have the same basename without extension as the
counts file but including *.json* or *.html* as appropriate. E.g., *counts.csv*
will produce *counts.json* and *counts.html* in the current directory. These
default filenames can be changed using optional command line arguments
``--json=<json fn>`` and ``--html=<html fn>`` as appropriate for all commands.
If ``<json fn>``, either default or specified, already exists, it is read in,
parsed, and added to.  The HTML report is overwritten on every invocation using
the contents of the JSON file.

.. _terminaltables: https://robpol86.github.io/terminaltables/
.. _json: http://www.json.org/

Tabular output format
---------------------

Each tool prints out the statistics it calculates to standard output by default.
The standard output format is comma separated values, e.g.::

    $ detk-stats base test_counts.csv
    stat,val
    num_cols,3
    num_rows,4

If desired, the ``-f table`` argument may be passed to pretty-print the table
instead::

    $ detk-stats base -f table test_counts.csv
    +base------+-----+
    | stat     | val |
    +----------+-----+
    | num_cols | 4   |
    | num_rows | 3   |
    +----------+-----+

The summary_ module is slightly different, as it executes multiple subtools.
The CSV output of the summary module adds a line starting with ``#`` before
each different output::

    $ detk-stats summary --bins=2 test_counts.csv
    #base
    stat,val
    num_cols,3
    num_rows,4
    #coldist
    colname,bin_50.0,bin_100.0,dist_50.0,dist_100.0
    a,55.0,100.0,2.0,2.0
    b,5500.0,10000.0,2.0,2.0
    c,550000.0,1000000.0,2.0,2.0
    #rowdist
    rowname,bin_50.0,bin_100.0,dist_50.0,dist_100.0
    gene1,50005.0,100000.0,2.0,1.0

The pretty-printed output simply outputs each table serially.

JSON output format
------------------

The JSON file produced by these modules is formatted as a JSON array containing
objects that each correspond to a stats module. For example::

  [
    {
      'name': 'base',
      'stats': {
        'num_cols': 50,
        'num_rows': 27143
      }
    },
    {
      'name': 'coldist',
      'stats': {
        'pct' : [ 0, 5, 10, 20, ...],
        'counts' : [
          {
            'name': 'H_0001',
            'counts': [ 129, 317, 900, 1325, ...]
            'frac': [ 0.01, 0.02, 0.04, 0.06, ...]
          },
          {
            'name': 'H_0002',
            'counts': [ 502, 127, 222, 591, ...]
            'frac': [ 0.05, 0.01, 0.02, 0.05, ...]
          }
        ]
      }
    },
    {
      'name': 'rowdist',
      'stats': ...
    }
    ...
  ]

The example above has been pretty-printed for visibility; the actual output is
written to a single line. The object format for each module is described in
detail below.

API Documentation
-----------------

.. _base:

``base`` - Basic statistics
+++++++++++++++++++++++++++
.. autoclass:: de_toolkit.stats.BaseStats
   :members: output

Command line usage::

    Usage:
        detk-stats base [options] <counts_fn>

    Options:
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>       Name of JSON output file
        --html=<html_fn>       Name of HTML output file

.. _coldist:

``coldist`` - Column-wise counts distributions
++++++++++++++++++++++++++++++++++++++++++++++
.. autoclass:: de_toolkit.stats.ColDist
   :members: output, properties

Command line usage::

    Usage:
        detk-stats coldist [options] <counts_fn>

    Options:
        --bins=N               The number of bins to use when computing the counts
                               distribution [default: 20]
        --log                  Perform a log10 transform on the counts before
                               calculating the distribution. Zeros are omitted
                               prior to histogram calculation.
        --density              Return a density distribution instead of counts,
                               such that the sum of values in *dist* for each
                               column approximately sum to 1.
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>       Name of JSON output file
        --html=<html_fn>       Name of HTML output file

.. _rowdist:

``rowdist`` - Row-wise counts distributions
+++++++++++++++++++++++++++++++++++++++++++
.. autoclass:: de_toolkit.stats.RowDist
   :members: output

Command line usage::

    Usage:
        detk-stats rowdist [options] <counts_fn>

    Options:
        --bins=N               The number of bins to use when computing the counts
                               distribution [default: 20]
        --log                  Perform a log10 transform on the counts before calculating
                               the distribution. Zeros are omitted prior to histogram
                               calculation.
        --density              Return a density distribution instead of counts, such that
                               the sum of values in *dist* for each row approximately
                               sum to 1.
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>       Name of JSON output file
        --html=<html_fn>       Name of HTML output file

.. _colzero:

``colzero`` - Column-wise statistics on zero counts
+++++++++++++++++++++++++++++++++++++++++++++++++++
.. autoclass:: de_toolkit.stats.ColZero
   :members: output, properties

Command line usage::

    Usage:
        detk-stats colzero [options] <counts_fn>

    Options:
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>       Name of JSON output file
        --html=<html_fn>       Name of HTML output file

.. _rowzero:

``rowzero`` - Row-wise statistics on zero counts
++++++++++++++++++++++++++++++++++++++++++++++++
.. autoclass:: de_toolkit.stats.RowZero
   :members: output, properties

Command line usage::

    Usage:
        detk-stats rowzero [options] <counts_fn>

    Options:
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>       Name of JSON output file
        --html=<html_fn>       Name of HTML output file


.. _entropy:

``entropy`` - Row-wise sample entropy calculation
+++++++++++++++++++++++++++++++++++++++++++++++++
.. autoclass:: de_toolkit.stats.Entropy
   :members: output, properties

Command line usage::

    Usage:
        detk-stats [options] entropy <counts_fn>

    Options:
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>       Name of JSON output file
        --html=<html_fn>       Name of HTML output file

.. _pca:

``pca`` - Principal component analysis
++++++++++++++++++++++++++++++++++++++
.. autoclass:: de_toolkit.stats.CountPCA
   :members: output, properties

Command line usage::

    Usage:
        detk-stats pca [options] <counts_fn>

    Options:
        -m FN --column-data=FN      Column data for annotating PCA results and
                                    plots (experimental)
        -f NAME --column-name=NAME  Column name from provided column data for
                                    annotation PCA results and plots (experimental)
        -o FILE --output=FILE       Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>            Name of JSON output file
        --html=<html_fn>            Name of HTML output file

.. _summary:

``summary`` - Common statistics set
+++++++++++++++++++++++++++++++++++
.. autofunction:: de_toolkit.stats.summary

Command line usage::

    Usage:
        detk-stats summary [options] <counts_fn>

    Options:
        -h --help
        --column-data=FN       Use column data provided in FN, only used in PCA
        --color-col=COLNAME    Use column data column COLNAME for coloring output plots
        --bins=BINS            Number of bins to use for the calculated
                               distributions [default: 20]
        --log                  log transform count statistics
        --density              Produce density distribution by dividing each distribution
                               by the appropriate sum
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        -f FMT --format=FMT    Format of output, either csv or table [default: csv]
        --json=<json_fn>       Name of JSON output file
        --html=<html_fn>       Name of HTML output file
