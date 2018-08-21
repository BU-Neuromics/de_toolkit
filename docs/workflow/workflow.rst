Workflow Tutorial
=================

There are a variety of functions and tools implemented in detk for differential
expression analysis. This example will assume that you have a raw counts matrix
file that you have obtained from an RNASeq analysis using appropriate upstream
tools, e.g. salmon_ transcriptome quantification or STAR_ + htseq-count_.

.. admonition:: Tool Tip

    If you have a pipeline that produces individual counts files for each
    of your samples, our command line tool csvgather_ may be helpful to
    easily combine these files together into a single matrix.

.. _salmon: https://combine-lab.github.io/salmon/
.. _STAR: https://github.com/alexdobin/STAR
.. _htseq-count: https://htseq.readthedocs.io/en/master/count.html
.. _csvgather: https://bitbucket.org/adamlabadorf/csvgather/src/master/

Using detk, we will perform the following steps:

1. examine statistics of the counts matrix using the :doc:`../stats` module
2. filter genes based on the statistics we gathered previously using the :doc:`../filter`
   module and mini-language
3. normalize the counts matrix with the DESeq2 normalization method using
   the :doc:`../norm` module
4. perform DESeq2 differential expression analysis for a condition of interest
   with the :doc:`../de` module

These pages contain a walkthrough tutorial of how to use detk for examining
and analyzing a counts matrix file, like those produced by an RNASeq
experiment.

.. toctree::
    :maxdepth: 2

    intro
    stats
    filtering
    normalization
    differential_expression
