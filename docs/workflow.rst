=================
Workflow Tutorial
=================

.. Contents::


Quick Start Guide
=================

There are a variety of functions and tools located in detk for differential expression analysis. This
example will assume that you have a counts matrix that you would like to perform filtering, normalization and
differential expression on called ``MyCounts``. Default behavior is to print the results to standard output. Detk assumes a input matrix  structure that looks like this...


+---------+----------+----------+
| gene_id | sample_1 | sample_2 |
+=========+==========+==========+
| gene_1  |    10000 |     1244 |
+---------+----------+----------+
| gene_2  |     2023 |     1534 |
+---------+----------+----------+
| gene_3  |        5 |        2 |
+---------+----------+----------+


Where information on the gene names  are in the 0th column, and the proceeding columns are samples with counts as rows.


Filtering
---------


Filtering should be done before normalization. There are three different filtering options available in
detk. **nonzero**, **mean**, and **median**. Command line arguments for filter take this form... 

::

  detk-filter [options] <command> [--column-data=<column data fn>] <counts_fn>


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


Normalization
-------------


Normalization is simple requiring only the count matrix you would like to normalize, and the name of the
output file

**Example**::

  detk-norm deseq2 ``MyFilteredCounts`` -o ``MyNormalizedCounts``


DESeq2 normalization is the only normalization strategy implemented currently

*Note*:

A csv file is created when specifying output with ``-o``


Differential Expression
-----------------------
Firth Logistic Expression
^^^^^^^^^^^^^^^^^^^^^^^^^
After normalization, differential expression can be performed. Currently only Firth's Logistic
Regression is implemented. Firth Logistic Regression requires three values. A design which specifies condition and covariates of interest in this form

**Without Covariates**::

  "Condition[VAR] ~ counts"


Alternatively covariates can be specified by adding them before ``counts`` separated by a ``+``. 

**With Covariates**::

  "Codition[VAR] ~ COV1+COV2+COVN+counts"

A meta data file with sample names, a cconditions and optionally covariates.

+--------------+-----------+-------------+
| sample_names | condition | covariate 1 |
+--------------+-----------+-------------+
| sample_1     | C1        | M           |
+--------------+-----------+-------------+
| sample_2     | C1        | F           |
+--------------+-----------+-------------+
| sample_3     | C2        | F           |
+--------------+-----------+-------------+
| sample_4     | C1        | F           |
+--------------+-----------+-------------+


**Example**::

  detk-de firth "Codition[VAR] ~ COV1+COV2+COVN+counts" MyNormalizedCounts MyInfoFile -o MyDifferentialExpression

*Note*:

A tsv file is created when specifying output with ``-o``
