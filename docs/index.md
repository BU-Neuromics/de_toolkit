# de_toolkit

`de_toolkit` (`detk`) is a suite of command line tools for common operations
on count matrices from high-throughput sequencing experiments — summary
statistics, filtering, normalization, transformation, differential expression,
and gene set enrichment. Tools are implemented in Python, or as thin wrappers
around canonical R packages ([DESeq2], [fgsea], [logistf]) via a
[lightweight R bridge](tools/wrapr.md) — no rpy2 required.

Every tool reads and writes plain delimited text files, making detk easy to
drop into any workflow manager (Snakemake, Nextflow, or a shell script). As a
side effect of each invocation, detk records machine-readable JSON describing
what was run and what it found, and can render everything into a single
self-contained HTML [report](report.md).

```bash
# normalize a counts matrix with the DESeq2 method
detk-norm deseq2 counts.csv > norm_counts.csv

# differential expression with a design formula
detk-de deseq2 "counts ~ AgeOfDeath + Status[control]" counts.csv samples.csv > de_results.csv
```

Head to the [Quickstart](quickstart.md) to see a full workflow,
the [worked example](example.md) for a real analysis ending in a
[live example report](example/detk_report.html), or
[Concepts](concepts.md) for the input file formats every tool shares.

## Installation

detk requires Python 3.10 or newer.

```bash
pip install de_toolkit
```

or, with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install de_toolkit
```

### R dependencies

The `de`, `enrich`, and some `norm`/`transform` subcommands wrap R packages.
You need R plus the following packages on your `PATH` to use them:

- [DESeq2] — `detk-de deseq2`, `detk-transform rlog`, `detk-transform vst`
- [fgsea] — `detk-enrich fgsea`
- [logistf] — `detk-de firth`

Install from within R:

```r
install.packages(c("BiocManager", "logistf", "jsonlite"))
BiocManager::install(c("DESeq2", "fgsea"))
```

or with conda/mamba from bioconda:

```bash
mamba install -c conda-forge -c bioconda \
    r-base r-jsonlite r-logistf bioconductor-deseq2 bioconductor-fgsea
```

Verify the R bridge is working with:

```console
$ detk wrapr check
R found: True
R path: /usr/bin/Rscript
jsonlite found: True
```

Everything else works without R.

## Development

```bash
git clone https://github.com/BU-Neuromics/de_toolkit.git
cd de_toolkit
uv sync          # creates .venv with the package + dev tools
uv run pytest    # run the test suite
```

Contributors without uv can use `pip install -e '.[test]'` in a virtualenv
instead. Tests that need R skip automatically when R is absent.

[DESeq2]: https://bioconductor.org/packages/release/bioc/html/DESeq2.html
[fgsea]: https://bioconductor.org/packages/release/bioc/html/fgsea.html
[logistf]: https://cran.r-project.org/package=logistf
