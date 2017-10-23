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

- mean:     
            Filter data based on the mean value of the row.
- median:   
            Filter data based on the median value of the row.
- zeros:    
            Filter data based on how many zero counts are in the row. If the 
            input number is between 0 and 1, (0 < number < 1), then the 
            number is the fraction of samples that must be zero. If the number
            is 1 or greater (1 <= number <= # of samples) or the number is equal
            to 0, then it is the number of samples that must be zero.
- nonzero:  
            Filter data based on how many nonzero counts are in the row. If the
            input number is between 0 and 1, (0 < number < 1), then the number
            is the fraction of samples that must be nonzero. If the number is 1
            or greater (1 <= number < # of samples) or the number is equal to 0,
            then it is the number of samples that must be nonzero.

Adding column data to filter
----------------------------

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

Using the column data, the filter module can then be run in two different ways.
The first way is to apply the filter to each group separately. If all groups 
fail the filter criteria, then that row is filtered out. In order to use this 
method, the command should be as follows::

  'mean(condition)>10'

The second way that you can specify the filter with column data is to filter 
rows based on a specific condition. The command would look like this where, 
'case' is a variable within the column data file (in the above example, this is
either test or control)::

  'mean(condition[case])>10'

Using the above column data example, to filter based on the 'test' group only,
the command would be::

  'mean(condition[test])>10
