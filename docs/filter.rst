``filter`` - Filtering Count Matrices
=====================================

Functions for filtering count matrices based on various criteria. 

The output is a file with rows filtered out of the original data based on a 
filter command. The module accepts a single counts file as input. By default, 
the output file has the same basename followed by '_filtered' and the same 
file extension as the input, so *counts.csv* will produce *counts_filtered.csv*.
The default output filename can be changed using the optional command line
argument '--output=<out_fn>'.

How to run the filter module
----------------------------

The filter module is run on the command line using the following::

    Usage:
        detk-filter [options] <command> <counts_fn> [<cov_fn>]

    Options:
        -o <out_fn> --output=<out_fn>    Name of output file [default: stdout]
        --column-data=<column_data_fn>   DEPRECATED: pass cov_fn as positional
                                     command line argument instead

The counts file is filtered based on the given command. Column data can also be
provided, and data can be filtered based on conditions specified in the column
data file. The filter module implements a custom mini language, which is used
to specify which and how gene should be filtered. The command must be
structured as follows, and enclosed in single or double quotes::

  <function>(<column spec>) <inequality> <number>

For example, to filter out rows that have a mean of less than 10 across all
samples, the command would be::

  mean(all) > 10

The command describes *rows that should be kept*. Those rows not meeting this
criteria are filtered out.

There are four different filter functions available:

- ``mean``:
            Filter data based on the mean value of the row or column spec.
- ``median``:
            Filter data based on the median value of the row or column spec.
- ``zeros``:
            Filter data based on how many zero counts are in the row. If the
            input number is between 0 and 1, (0 < number < 1), then the 
            number is the fraction of samples that must be zero. If the number
            is 1 or greater (1 <= number <= # of samples) or the number is equal
            to 0, then it is the number of samples that must be zero.
- ``nonzero``:
            Filter data based on how many nonzero counts are in the row. If the
            input number is between 0 and 1, (0 < number < 1), then the number
            is the fraction of samples that must be nonzero. If the number is 1
            or greater (1 <= number < # of samples) or the number is equal to 0,
            then it is the number of samples that must be nonzero.

The column spec value can take one of three forms:

- ``all``: literal value indicating filter should be applied across all columns
- column name from a column data file (see below)
- column name from a column data file with a group value specified (see below)

The inequalities supported are: ``>``, ``>=``, ``<``, ``<=``, ``==``, and
``!=``. Numbers can be positive or negative integer or floating point numbers.

White spaces are disregarded, so the following are equivalent::

  mean(all)>10
  mean(all) > 10

Additionally, multiple terms can be input at once to filter on more than one 
criteria at a time using the keywords ``and`` or ``or``. For example::

  mean(all) > 10 and zeros(all) < 0.5

This filter will include all genes with greater than an overall mean of 10 and
with more than 50% of the samples having nonzero counts. Commands may be
arbitrarily grouped to create complex filtering rules::

  (mean(all) > 5 and nonzero(all) > 0.9) or mean(all) > 100

This filter will identify lowly but consistenly (i.e. non-zero) abundant rows
and any rows with more than a mean of 100 counts across all samples. The
ability to group filters together becomes much more powerful when incorporated
with column data.

Incorporating column data into filter
-------------------------------------

A column data file can be optionally input to the filter module. The column data
file should specify subsets of the samples that the filter can then be applied
to separately. The first column of the file must match the sample names given
in the counts file. For example, if your counts file contains samples 'A', 'B',
'C', and 'D', a column data file might look like this::

  sample_name, condition
  A, test
  B, test
  C, test
  D, control
  E, control

Using the column data, the filter module can then be run in two different ways.
The first way is to apply the filter to each group separately. If *all groups 
fail* the filter criteria, then that row is filtered out. In order to use this 
method, the command should be as follows::

  mean(condition) > 10

The ``condition`` column spec above corresponds to the condition column in the
column data file. This filter will retain genes that have a mean count greater
than 10 within *either* the test samples *or* the control samples. This enables
powerful and expressive filtering schemes, for example::

  nonzero(condition) > 0.5

This filter retains genes that have fewer than 50% zero counts in either
condition, so genes that are uniquely expressed in test or control will proceed
to downstream analysis. Filtering on overall mean may eliminate these very
interesting genes from consideration.

The second way that you can specify the filter with column data is to filter
rows based on a specific condition. The command includes a value that subsets
the columns of the counts matrix so that filters can be applied to specific
groups::

  mean(condition[test]) > 10

This filter will retain genes that have a mean count greater than 10 in the
test samples, regardless of the counts in the control samples.
