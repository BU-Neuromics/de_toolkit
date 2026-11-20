# Tutorials

Each tutorial is a complete session you can follow at the command line:
every command on the page runs in order, from an empty directory, and the
outputs the page shows are what you should see. The same pages run as
detk's integration tests, so a tutorial that no longer works fails the
test suite before it reaches you.

| Tutorial | What it covers | Needs |
| --- | --- | --- |
| Differential expression on airway | statistics, filtering, DESeq2 normalization, VST, outliers, `detk-de deseq2`, gene symbols, the report and the crate | detk, R with DESeq2 and airway |
| [From quantifier outputs to a normalized matrix](quantifiers.md) | gathering salmon `quant.sf` files, a sample sheet, CPM and TPM, transforms, statistics and the report | detk only |
| Derived covariates and recorded steps | deriving covariates with Miller, recording each step with `detk-util record`, using a derived covariate in a DESeq2 design | detk, R with DESeq2 and airway, [Miller](https://miller.readthedocs.io/) (`mlr`) |

The tutorials are being written for detk 1.0; each row links to its page
once the page is in place.

## Following a tutorial

Start in an empty directory with detk installed (see the
[quickstart](../quickstart.md)), and run the commands in the order the page
shows them. A tutorial that needs R expects `Rscript` on your `PATH` with the
listed packages installed; one that needs Miller expects `mlr`.

## Running a tutorial as a test

From a checkout of the repository, run one tutorial by name:

```console
$ uv run pytest tests/tutorials -k quantifiers
```

or all of them with `uv run pytest tests/tutorials`. A tutorial whose
requirements (R, an R package, Miller) are missing is skipped, with the
reason shown by `pytest -rs`.
