First detk principles
=====================

By: Adam Labadorf

detk is a collection of functions and methods that are commonly used in
differential expression analysis. Normally, most of these functions are
performed either by separate programs, often written in different languages, or
implemented manually using custom code using your favorite language and tools.
After enough moments thinking to myself, *"Didn't I already write this exact
code a dozen times already?!*, I decided to get busy getting lazy and, with the
help of others, designed and wrote this package.

The primary goals of this package are three fold:

1. provide an easy-to-use command line interface for common operations on
   counts matrix files that is easy to integrate into workflows, e.g.
   snakemake_ or Nextflow_
2. make the results of these common counts matrix operations more consistent
   and less error prone, due to not repeatedly implementing the same custom
   code
3. avoid writing R

.. _snakemake: https://snakemake.readthedocs.io/en/stable/
.. _Nextflow: https://www.nextflow.io/

The two core concepts of this package are the *counts matrix file* and
the *metadata file*, described below.

The Count Matrix
----------------

Every tool in detk accepts a counts matrix file of the form:

+---------+----------+----------+---+----------+
| gene_id | sample_1 | sample_2 |...| sample_m |
+=========+==========+==========+===+==========+
| gene_1  |    10000 |     1244 |...|     2935 |
+---------+----------+----------+---+----------+
| gene_2  |     2023 |     1534 |...|     1308 |
+---------+----------+----------+---+----------+
| gene_3  |        5 |        2 |...|       19 |
+---------+----------+----------+---+----------+
| ...     |      ... |      ... |...|   ...    |
+---------+----------+----------+---+----------+
| gene_n  |        5 |        2 |...|   150031 |
+---------+----------+----------+---+----------+

The first column must be unique gene or feature identifiers, e.g. Ensembl Gene
IDs, miRBase IDs, ChIPSeq peaks, unique genomic bins, etc. The columns must be
unique sample identifiers. The column name of the first column doesn't matter,
(could be blank I guess) but each row must have the same number of columns. The
format must be character delimited, but detk sniffs the format so the delimiter
can, in principle, be any single character. However, for consistency, detk
always outputs results using comma separated format, so, you should probably
use that.


The Column Metadata File
------------------------

Other detk functions require metadata on each of the samples to perform certain
analyses, e.g. differential expression. The metadata file, or column data file,
should be a character delimited text file with the following form:

+--------------+-----------+-----+-----+-------------+
| sample_names | condition | sex | ... | covariate_p |
+--------------+-----------+-----+-----+-------------+
| sample_1     | case      |  M  | ... |     c1      |
+--------------+-----------+-----+-----+-------------+
| sample_2     | control   |  F  | ... |     c9      |
+--------------+-----------+-----+-----+-------------+
| ...          | ...       | ... | ... |     ...     |
+--------------+-----------+-----+-----+-------------+
| sample_m     | case      | F   | ... |     c3      |
+--------------+-----------+-----+-----+-------------+

The first column should contain sample names, and remaining columns hold any
information about the samples that might be needed for analysis. In this
example, the ``condition`` column might indicate whether the sample is a
disease or healthy subject. Although detk will attempt to match up the sample
names in the first column of the metadata file with the column names of the
corresponding counts file, it is good practice to create these files such
that the order agrees. detk will sniff the format of the file you provide,
so it may be delimited with any single character you wish.
