Filtering a Counts Matrix File
==============================

Filtering should be done before normalization. There are three different
filtering options available in detk. **nonzero**, **mean**, and **median**.
Command line arguments for filter take this form::

  detk-filter [options] <filter commands> [--column-data=<column data fn>] <counts_fn>


The structure of the filter command is as follows..

::

  <function>(all or condition) <inequality> <number>

  
So to if you wanted to only keep rows in the matrix where the means where greater than 10, you would specify

``'mean(all)>10'``

On the command line. Spacing does not matter and ``'mean(all) > 10'`` is functionally equivalent to the previous command.

**Example**::

    detk-filter -o MyFilteredCounts 'mean(all)>10' MyCounts

    
*Note*:

The command describes keeping rows based on meeting the above condition. A csv file is created when specifying output with ``-o``


More detailed information on other methods can be found in the **filter.rst** file.


