# airway example

The airway analysis is the tutorial
[`docs/tutorials/airway.md`](../../docs/tutorials/airway.md), published at
<https://bu-neuromics.github.io/de_toolkit/tutorials/airway/>: the page holds
the commands, with the outputs to expect, and detk's tests run it (in the CI
job with R).

`run.sh` regenerates the published example report from that page: it runs
the page as its test does and copies the report and the provenance crate the
run made into `docs/example/`, served at
<https://bu-neuromics.github.io/de_toolkit/example/detk_report.html>.

```bash
examples/airway/run.sh
```

It needs uv and R on `PATH` with the Bioconductor packages DESeq2, airway and
org.Hs.eg.db (the tutorial shows a conda command that installs them). The
run's working directory, with every file the page made, is left in
`examples/airway/run/airway0/`.

The dataset: GEO [GSE52778](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778),
Himes BE et al. *RNA-Seq transcriptome profiling identifies CRISPLD2 as a
glucocorticoid responsive gene that modulates cytokine function in airway
smooth muscle cells.* PLoS One 2014, PMID 24926665; counts from the
[airway](https://bioconductor.org/packages/airway/) Bioconductor data
package.
