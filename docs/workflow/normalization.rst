Normalization
-------------

Normalization is simple requiring only the count matrix you would like to normalize, and the name of the
output file

**Example**::

  detk-norm deseq2 ``MyFilteredCounts`` -o ``MyNormalizedCounts``


DESeq2 normalization is the only normalization strategy implemented currently

*Note*:

A csv file is created when specifying output with ``-o``

