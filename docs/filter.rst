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

  detk-filter [options] <command> [--column-data=<column data fn>] <counts_fn>

  Options:
    --output=<out_fn>  Output file name

The counts file is filtered based on the given command. Column data can also be
provided, and data can be filtered based on conditions specified in the column
data file. The filter module implements a custom python mini language, which is
used to interpret the command input. The command must be structured as follows,
and enclosed in single or double quotes::

  <function>(all or condition) <inequality> <number>

Keep in mind that the command describes rows that should be kept. Those rows not
meeting this criteria are filtered out. For example, to filter out rows that 
have a mean of less than 10, the command should be::

  'mean(all) > 10'

White spaces are disregarded, so the following are equivalent::

  'mean(all)>10' and 'mean(all) > 10'

Additionally, multiple terms can be input at once to filter on more than one 
criteria at a time using the keywords 'and' or 'or'. For example::

  'mean(all)>10 and zeros(all)<0.5'

Filter functions
----------------

There are four different filter functions that are available:

- mean:     Filter data based on the mean value of the row.
- median:   Filter data based on the median value of the row.
- zeros:    Filter data based on how many zero counts are in the row. If the 
            input number is between 0 and 1, (0 <= number < 1), then the 
            number is the fraction of samples that must be zero. If the number
            is 1 or greater (1 <= number <= # of samples), then it is the 
            number of samples that must be zero.
- nonzero:  Filter data based on how many nonzero counts are in the row. If the
            input number is between 0 and 1, (0 <= number < 1), then the number
            is the fraction of samples that must be nonzero. If the number is 1
            or greater (1 <= number < # of samples), then it is the number of 
            samples that must be nonzero.
