``norm`` - Normalizing Count Matrices
=====================================

Count normalization strategies.

``deseq2`` normalization
------------------------

Normalize the provided counts matrix using the method as implemented in the R
package DESeq2_. Briefly, each sample is divided by a size factor calculated
as the median ratio of each gene count divided by the geometric mean count
across all samples. The implementation here is a python port of the R version,
and is roughly equivalent to the following R code:

.. code-block:: R

    library(DESeq2)

    counts <- as.matrix(read.table(counts.fn,row.names=1))
    colData <- data.frame(name=seq(ncol(counts)))

    dds <- DESeqDataSetFromMatrix(
        countData=counts,
        colData=colData,
        design = ~ 1
    )

    dds <- estimateSizeFactors(dds)
    write.table(counts(dds,normalized=TRUE),norm.counts.fn)

Usage::

    Perform counts normalization on the given counts matrix using the method
    implemented in the DESeq2 package.

    Usage:
        detk-norm deseq2 [options] <counts_fn>

    Options:
        -h --help                    Print out this help
        -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
        --size-factors=FILE          Write out the size factors found by the DESeq2
                                     method to two column tab separated file where
                                     the first column is sample name and the second
                                     column is the size factor


.. _DESeq2: https://bioconductor.org/packages/release/bioc/html/DESeq2.html

``library`` size normalization
------------------------------

Normalize each counts column by the sum of total counts in that column. Usage::

    Perform library size normalization on the columns of the given counts matrix.
    Counts in each column are divided by the sum of each column.

    Usage:
        detk-norm library [options] <counts_fn>

    Options:
        -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]

``fpkm`` normalization
----------------------

Normalize each gene count according to the Fragments Per Kilobase per Million
reads normalization procedure as described `here <fpkm>`_. Briefly, each count
is divided first by the length of the gene in bases divided by 1000, and then
divided by the number of reads in the sample divided by one million.

In order to normalize each gene by its effective gene length, detk must be
provided the lengths for every gene/feature identifier found in the counts
file. These lengths should be supplied in the form of a two-column character
delimited text file (tabs, commas, whatever, etc, detk sniffs the format) where
the first column is the gene identifier and the second column is the gene
length in bases.

* Every gene in the counts file must have an entry in the lengths file
* The lengths file may have unused gene lengths
* The order of genes between files do not have to match

Usage::


    Perform Fragments Per Kilobase per Million normalization on the given counts
    file. <lengths_fn> should be a delimited file with two columns, the first
    being the name of one of the rows in the counts file and the second is the
    effective length of the gene/sequence/etc to use in the normalization.

    *Note:* Program will throw an error and exit if there are genes/sequences
    in the counts file that are not found in the lengths file.

    The order of names in the counts and lengths files do *not* have to be the
    same.

    Usage:
        detk-norm fpkm [options] <counts_fn> <lengths_fn>

    Options:
        -o FILE --output=FILE  Destination of normalized output in CSV format [default: stdout]


.. _fpkm: https://www.rna-seqblog.com/rpkm-fpkm-and-tpm-clearly-explained/
