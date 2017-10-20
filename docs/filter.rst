``filter`` - Filtering Count Matrices
=====================================

Functions for filtering count matrices based on various criteria. 

The output is a file with rows filtered out of the original data based on a 
filter command. The module accepts a single counts file as input. By default, 
the output file has the same basename followed by '_filtered' and the same 
file extension as the input, so *counts.csv* will produce *counts_filtered.csv*.
The default output filename can be changed using the optional command line
argument '--output=<out_fn>'.

How to run filter
-----------------

