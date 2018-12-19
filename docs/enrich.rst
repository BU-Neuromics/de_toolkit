``enrich`` - Set Enrichment Methods
===================================

.. contents::
    :local:

Functions for performing statistical set enrichment methods, e.g.
Gene Set Enrichment Analysis

``fgsea``
-----------
.. autofunction:: de_toolkit.enrich.fgsea

Command line usage::

    Perform preranked Gene Set Enrichment Analysis using the fgsea bioconductor
    package on the given gmt gene set file.

    The GMT file must be tab delimited with set name in the first column, a
    description in the second column (ignored by detk), and an individual feature
    ID in each column after, one feature set per line. The result file can be any
    character delimited file, and is assumed to have column names in the first row.

    The feature IDs must be from the same system (e.g. gene symbols, ENSGIDs, etc)
    in both GMT and result files. The user will likely have to provide:

    - -i <col>: column name in the results file that contains feature IDs, e.g.
      gene_name
    - -c <col>: column name in the results file that contains the statistics to
      use when computing enrichment, e.g. log2FoldChange

    fgsea: https://bioconductor.org/packages/release/bioc/html/fgsea.html

    Usage:
        detk-enrich fgsea [options] <gmt_fn> <result_fn>

    Options:
        -h --help                 Print out this help
        -o FILE --output=FILE     Destination of fgsea output [default: stdout]
        -p PROCS --cores=PROCS    Ask BiocParallel to use PROCS processes when
                                  executing fgsea in parallel, requires the
                                  BiocParallel package to be installed
        -i FIELD --idcol=FIELD    Column name or 0-based integer index to use as
                                  the gene identifier [default: 0]
        -c FIELD --statcol=FIELD  Column name or 0-based integer index to use as
                                  the statistic for ranking, defaults to the last
                                  numeric column in the file
        -a --ascending            Sort column ascending, default is to sort
                                  descending, use this if you are sorting by p-value
                                  or want to reverse the directionality of the NES
                                  scores
        --abs                     Take the absolute value of the column before
                                  passing to fgsea
        --minSize=INT             minSize argument to fgsea [default: 15]
        --maxSize=INT             maxSize argument to fgsea [default: 500]
        --nperm=INT               nperm argument to fgsea [default: 10000]
        --rda=FILE                write out the fgsea result to the provide file
                                  using saveRDS() in R
