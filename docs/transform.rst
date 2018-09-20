``transform`` - Count Transformation
====================================

.. contents::
    :local:

Transformations of the distribution of counts in a matrix.

``plog``
--------

.. autofunction:: de_toolkit.transform.plog


Command line usage::

    Usage:
        detk-transform plog [options] <count_fn>

    Options:
        -c N --pseudocount=N   The pseudocount to use when taking the log transform [default:1]
        -b B --base=B          The base of the log to use [default: 10]
        -o FILE --output=FILE  Destination of primary output [default: stdout]

``rlog``
--------

Command line interface to the DESeq2_ Regularized log (``rlog``)
transformation. As in the originating package, the default behavior is to
perform a blind transformation, i.e. without respect to an experimental
design::

    detk-transform rlog norm_counts.csv > rlog_norm_counts.csv

Roughly equivalent to the following R code:

.. code-block:: R

    library(DESeq2)

    cnts <- as.matrix(read.csv("norm_counts.csv",row.names=1))
    fakeColData <- # fake column data...

    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = fakeColData,
        design = ~ 1
    )

    dds <- rlog(dds,blind=True)
    write.csv(assay(dds),out.fn)

To perform a non-blind transformation, a formula and column data file may be
provided::

    detk-transform rlog norm_counts.csv "counts ~ AgeOfDeath + Status" column_data.csv > rlog_norm_counts_nonblind.csv

This invocation is roughly equivalent to the following R code:

.. code-block:: R

    library(DESeq2)

    cnts <- as.matrix(read.csv("norm_counts.csv",row.names=1))
    colData <- read.csv("column_data.csv",header=T,as.is=T,row.names=1)

    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = ~ AgeOfDeath + Status
    )

    dds <- rlog(dds,blind=False)
    write.csv(assay(dds),out.fn)


.. _DESeq2: https://bioconductor.org/packages/release/bioc/html/DESeq2.html


``vst``
-------

Command line interface to the DESeq2_ Regularized log (``vst``)
transformation::

    detk-transform vst norm_counts.csv > vst_norm_counts.csv

Roughly equivalent to the following R code:

.. code-block:: R

    library(DESeq2)

    cnts <- as.matrix(read.csv("norm_counts.csv",row.names=1))
    fakeColData <- # fake column data...

    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = fakeColData,
        design = ~ 1
    )

    dds <- vst(dds)
    write.csv(assay(dds),out.fn)


