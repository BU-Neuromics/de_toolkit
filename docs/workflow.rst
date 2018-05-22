=================
Workflow Tutorial
=================


Standard Workflow
=================


Quick Start Guide
-----------------

There are a variety of functions and tools located in detk for differential expression analysis. This
example will assume that you have a counts matrix that you would like to perform normalization and
differential expression on a counts matrix called ``MyCounts``. Detk assumes a file structure that
looks like this...


+---------+----------+----------+
| gene_id | sample_1 | sample_2 |
+=========+==========+==========+
| gene_1  |    10000 |     1244 |
+---------+----------+----------+
| gene_2  |     2023 |     1534 |
+---------+----------+----------+
| gene_3  |        5 |        2 |
+---------+----------+----------+


Where information on the gene names  are in the 0th column, and the proceeding columns are samples.


Filtering
---------


Filtering should be done before normalization. There are three different filtering options available in
detk. nonzero, mean, and median. The command line arguments for filter are... 


  detk-filter [options] <command> [--column-data=<column data fn>] <counts_fn>


The structure of the filter command is as follows


  <function>(all or condition) <inequality> <number>

  
``'mean(all)>10'`` and ``'mean(all) > 10'`` spaces are not counted so the two commands are functionally
equivalent.


    detk-filter -o MyFilteredCounts 'mean(all)>10' MyCounts

    
*Note*
The command describes rows that are kept based on meeting the condition described


More detailed information on filtering can be found in the filter.rst


Normalization
-------------


Normalization is simple requiring only the count matrix you would like to normalize, and the name of the
output file


  detk-norm deseq2 ``MyFilteredCounts`` -o ``MyNormalizedCounts``


DESeq2 normalization is the only normalization strategy implemented currently


Differential Expression
-----------------------

After normalization, differential expression can be performed. Currently only Firth's Logistic
Regression is implemented. The input requires a design. The design is surrounded by quotations with the
condition on oneside and the the covariates and counts on the other.


  "Condition[VAR] ~ counts"


Alternatively covariates can be specified by adding them before ``counts`` separated by a ``+``. 


  "ColumnOfInterest ~ COV1+COV2+COVN+counts"


In the sample info file, the first column must contains names of the samples. They must match the names
in the counts matrix. The next column will be the condition of each sample. Each subsequent column will
correspond to a covariate.

  detk-de firth "MyDesign" MyNormalizedCounts MyInfoFile -o MyDifferentialExpression
