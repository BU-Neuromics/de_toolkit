# Introduction

This is a collection of utilities to perform various operations on genomic
count datasets involving determining differential expression. Submodules
are:

  * norm - various normalization strategies, including:
    - DESeq2
    - trimmed mean
    - reference norm
    - library size
    - FPKM
    - user supplied
  * de - compute differential expression, using one of:
    - DESeq2
    - Firth's Logistic Regression
    - t-test
  * outlier - operations and statistics concerning potential outliers
    - entropy
    - Cook's distance
  * transform - transform counts into other forms
    - DESeq2 Variance Stabilizing Transform
    - RUVSeq transformation
    - trim
    - shrink
  * filter - filter genes based on statistics
    - nonzero
    - mean
  * stats - numerous statistics on the counts
    - summary
    - dist
    - PCA

# Installing

## conda package

We suggest installing this package using [anaconda](http://anaconda.org) on the
bubhub channel:

```
conda install -c bubhub de_toolkit
```

## Manual installation

If conda is not available, ensure the following packages are installed and
available in your environment:

  * python packages (python>=3.5):
    - docopt
    - pandas
    - numpy
  * R packages (R>=3.2):
    - R>=3.2
    - docopt

The following packages are only required to use the corresponding submodule
functions:

  * R packages:
    - DESeq2 (bioconductor)
    - RUVSeq (bioconductor)
    - logistf (CRAN)
