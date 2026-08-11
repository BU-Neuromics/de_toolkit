[![CI](https://github.com/BU-Neuromics/de_toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/BU-Neuromics/de_toolkit/actions/workflows/ci.yml)
[![docs](https://img.shields.io/badge/docs-latest-blue)](https://bu-neuromics.github.io/de_toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/de_toolkit)](https://pypi.org/project/de_toolkit/)
<!-- NOTE: the PyPI badge shows the stale 0.9.12 release until the 1.0.0 release is published -->

# Introduction

This is a collection of utilities to perform various operations on genomic
count datasets involving determining differential expression.

# Documentation

Documentation is at:

- [bu-neuromics.github.io/de_toolkit](https://bu-neuromics.github.io/de_toolkit/)

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

The project is managed with [uv](https://docs.astral.sh/uv/):

```
cd de_toolkit
uv sync        # create .venv with the package and dev tools
uv run pytest  # run the test suite
```

If you don't use uv, a plain virtualenv works too: `pip install -e '.[test]'`,
then `pytest`. Lint and format with `uv run ruff check .` and
`uv run ruff format .`; docs preview with `uv run --group docs mkdocs serve`.

Tests that require R (DESeq2, fgsea, logistf) are skipped automatically when R
is not available.
