# Introduction

This is a collection of utilities to perform various operations on genomic
count datasets involving determining differential expression.

# Documentation

There is work-in-progress documentation at (readthedocs.org):

- [de_toolkit](http://de-toolkit.readthedocs.io/en/latest/)

# Installing

## From pypi

```
pip install de_toolkit
```

## Installing R and packages

Certain functions in detk, particularly the `de`, `enrich`, and `transform`
modules, interface with R and Bioconductor packages. You must have a version of
R installed along with the following packages to use the corresponding
submodule functions:

  - [DESeq2](https://bioconductor.org/packages/release/bioc/html/DESeq2.html)
  - [fgsea](https://bioconductor.org/packages/release/bioc/html/fgsea.html)
  - [logistf](https://cran.r-project.org/web/packages/logistf/index.html)

The Bioconductor packages can be installed from within R with:

```r
install.packages("BiocManager")
BiocManager::install(c("DESeq2", "fgsea"))
install.packages("logistf")
```

# Development

detk requires Python 3.10 or newer. First fork and/or clone this repo:

```
git clone https://github.com/BU-Neuromics/de_toolkit.git
```

We suggest working in a virtual environment, then installing the package in
editable mode with its test dependencies:

```
cd de_toolkit
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
```

This makes `detk` and its subtools available on the command line. Because the
install is editable, code changes take effect without reinstalling. Run the
test suite with:

```
pytest
```

Tests that require R (DESeq2, fgsea, logistf) are skipped automatically when R
is not available.
