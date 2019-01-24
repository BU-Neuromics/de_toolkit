``de`` - Differential Expression
================================

.. important::

    The model formulas in this module use the :doc:`patsy_lite` mini-language. Be sure to read that first before writing your models!
    
    Also remember to filter prior to differential expression analysis. The number of genes provided for hypothesis testing may affect the results.
    You may need to filter out genes that have zero expression in all of the samples you are interested in.

Differential expression tools. Each of these mthods accepts a design formula, a
counts matrix file, and a column data file. The design formula is specified
using the :doc:`patsy_lite` mini-language. The counts and column data matrices
must be formatted as with any other tool in detk.

``deseq2``
----------

.. sidebar:: Note

    If you are only interested in a subset of the samples, you can still provide the whole raw count matrix and a 
    column data table with the samples you care about.

Command line interface to a canonical DESeq2_ analysis. To run a DESeq2
analysis on a counts matrix and accompanying column data file::

    detk-de deseq2 "counts ~ AgeOfDeath + Status" raw_counts.csv column_data.csv > deseq2_results.csv

.. _DESeq2: https://bioconductor.org/packages/release/bioc/html/DESeq2.html

This is roughly equivalent to the following R:

.. code-block:: R

    library(DESeq2)

    counts <- read.csv("raw_counts.csv",rownames=1)

    design.mat <- read.csv("column_data.csv")

    dds <- DESeqDataSetFromMatrix(
        countData = counts,
        colData = design.mat,
        design = ~ AgeOfDeath + Status
    )

    dds <- DESeq(dds, minReplicatesForReplace=Inf)

    write.csv(results(dds,cooksCutoff=Inf),de.out.fn)

**The analysis implemented here differs from the default DESeq2 analysis** in
the following ways:

* the design formula specified on the command line *must* have the value
  ``counts`` as the only term of the left hand side
* no outlier mean trimming based on Cooks distance is performed
* no p-values or adjusted p-values are flagged or omitted due to outliers
* estimated parameters, statistics, and p-values are reported for
  *all variables in the model* in the output, rather than just the last term
  (request the default behavior using the ``--last-term-only`` command line
  flag)
* no independent filtering is performed
* all columns related to a term in the model have the term name prepended
  in the output, e.g. ``Status__log2FoldChange``

Usage::

    Usage:
        detk-de deseq2 [options] <design> <count_fn> <cov_fn>

    Options:
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        --rda=RDA              Filename passed to saveRDS() R function of the result
                               objects from the analysis
        --strict               Require that the sample order indicated by the column names in the
                               counts file are the same as, and in the same order as, the
                               sample order in the row names of the covariates file
        --norm-counts          Prevent DESeq2 from normalizing counts prior to
                               running differential expression, default behavior
                               assumes that provided counts are raw
        --last-term-only       Use the default DESeq2 behavior of returning DE parameters
                               for the last term in the model, default behavior is to
                               report parameters for all variables in the model
        --gene-wise-disp       Use estimateDispersionsGeneEst instead of estimateDispersions
        --cores=N              Tell DESeq2 to use N cores when running, requires the
                               BiocParallel Bioconductor package to be installed [default: none]

``firth`` logistic regression
-----------------------------

When performing differential expression comparing two classes of samples,
`Firth's logistic regression`_ as described by `Choi et al`_ has desirable
statistical properties including a better controlled type I error rate and
less loss of power due to including additional variables in the model compared
with other DE methods, including DESeq2_. This form of logistic regression uses
a penalized likelihood method to avoid the problem of `complete separation`_ of
the data, a common occurence in RNASeq data. One drawback of the method is it
requires more samples than DESeq2 and other negative binomial regression based
methods (i.e. at least 10 replicates per condition).

.. _Firth's logistic regression: https://onlinelibrary.wiley.com/doi/abs/10.1002/sim.1047
.. _Choi et al: https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-017-1498-y
.. _complete separation: https://stats.idre.ucla.edu/other/mult-pkg/faq/general/faqwhat-is-complete-or-quasi-complete-separation-in-logisticprobit-regression-and-how-do-we-deal-with-them/

A ``counts`` term must be included on the right hand side of the design formula.

::

    detk-de firth "Status ~ AgeOfDeath + counts" norm_counts.csv column_data.csv > firth_results.csv


Usage::

    Usage:
        detk-de firth [options] <design> <count_fn> <cov_fn>

    Options:
        -o FILE --output=FILE  Destination of primary output [default: stdout]
        --rda=RDA              Filename passed to saveRDS() R function of the result
                               objects from the analysis
        --strict               Require that the sample order indicated by the column names in the
                               counts file are the same as, and in the same order as, the
                               sample order in the row names of the covariates file
        --standardize          Standardize counts prior to running logistic regression
                               as to obtain standardized (i.e. directly comparable)
                               beta coefficients
        --cores=N              Tell R to use N cores when running, requires the
                               parallel R package to be installed [default: none]

