=================
Workflow Tutorial
=================


Standard Workflow
=================


Quick Start Guide
-----------------


Filtering
---------

Filtering should be done before normalization. There are three different filtering options available in
detk. nonzero, mean, and median.

The structure of the filter command is as follows

  <function>(all or condition) <inequality> <number>

More detailed information on filtering can be found filtering.rst_


There are a variety of functions and tools located in detk for differential expression analysis. This
example will assume that you have a counts matrix that you would like to perform normalization and
differential expression called ``MyCounts``. Detk assumes a file structure that looks like this


+---------+----------+----------+
| gene_id | sample_1 | sample_2 |
+=========+==========+==========+
| gene_1  |    10000 |     1244 |
+---------+----------+----------+
| gene_2  |     2023 |     1534 |
+---------+----------+----------+
| gene_3  |        5 |        2 |
+---------+----------+----------+

Where gene ids are in the 0th column, and the proceeding columns are samples. Performing a DESeq2
normalization is simple, requiring the user only to specify an input and output file.
 

  detk-norm deseq2 ``MyCounts`` -o ``MyNormalizedCounts``



After normalization, differential expression can be performed. Currently only Firth's Logistic
Regression is implemented. The input requires a design. The design is surrounded by quotations with the
variable of interest on oneside and the the covariates and counts on the other

  "ColumnOfInterest[VAR] ~ counts"

Alternatively covariates can be specified by adding them before ``counts`` separated by a ``+``. 

  "ColumnOfInterest ~ COV1+COV2+COVN+counts"

Covariates and the column of interest must match the column names in the sample info file exactly. 

  detk-de firth "MyDesign" MyNormalizedCounts MyInfoFile -o MyDifferentialExpression
