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

# Documentation

There is work-in-progress documentation at (readthedocs.org):

- [de_toolkit](http://de-toolkit.readthedocs.io/en/latest/)

# Installing

## From pypi

```
pip install de_toolkit
```

## Installing R and packages

Certain functions in detk, particularly the `de` module, use rpy2 to interface
with R and bioconductor packages. You must have a version of R installed and
the following packages to use the corresponding submodule functions:

  - [DESeq2](https://bioconductor.org/packages/release/bioc/html/DESeq2.html)
  - [logistf](https://cran.r-project.org/web/packages/logistf/index.html)

# Development

First clone or fork and clone this repo:

```
git clone https://bitbucket.org/bubioinformaticshub/de_toolkit.git
```

We suggest using [anaconda](http://anaconda.org) to create an environment that
contains the software necessary, e.g.:

```
cd de_toolkit
conda create -n de_toolkit python=3.5
source activate de_toolkit
./install_conda_packages.sh
Rscript install_r_packages.R
```

In development, when you want to run the toolkit, use the `setup.py` script:

```
python setup.py install
```

This should make the `detk` and its subtools available on the command line. Whenever you make changes
to the code you will need to run this command again.
