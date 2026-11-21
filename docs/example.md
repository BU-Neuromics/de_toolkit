# Worked example: the airway dataset

detk's example report is a complete differential expression analysis of a
real, public RNA-seq dataset, **airway** (GEO
[GSE52778](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778)):
human airway smooth muscle cells from four donor cell lines, treated with
dexamethasone or untreated, 8 samples and 63,677 Ensembl genes, from the
[airway](https://bioconductor.org/packages/airway/) Bioconductor data package
(Himes et al. 2014, PMID 24926665).

**[Open the finished example report](example/detk_report.html)**: one
self-contained HTML file, everything client-side, nothing leaves your
browser.

The run's machine-readable provenance is published alongside it:
[`ro-crate-metadata.json`](example/ro-crate-metadata.json), a
[Process Run Crate](report.md#standards-based-provenance-the-process-run-crate)
describing every step of the run.

## How it was made

The tutorial [Differential expression on airway](tutorials/airway.md) is the
whole analysis, step by step, with the output to expect at each one: getting
the data, summary statistics, filtering, DESeq2 normalization, the
variance-stabilizing transform, entropy outliers, `detk-de deseq2` with the
cell line as a covariate, gene symbols, and the report and the crate. detk's
tests run that page, and the report above is the one its run made
(`examples/airway/run.sh` in the repository runs the page and publishes the
report here).

## Using a workflow manager

Each step is a plain command-line filter, so the pipeline drops directly into
Snakemake, Nextflow, or a shell script — see the
[Quickstart](quickstart.md#using-a-workflow-manager) for a Snakemake version
of this same shape.
