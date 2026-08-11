# Worked example: the airway dataset

This walkthrough runs the full detk toolkit on a real, public RNA-seq dataset
and ends with the report you can view right now:

<div style="text-align:center; margin: 1em 0;">
  <a href="example/detk_report.html" style="font-size:1.15em; font-weight:600;">
  → open the finished example report ←</a><br>
  <small>(self-contained HTML — everything client-side, nothing leaves your browser)</small>
</div>

The run's machine-readable provenance is published alongside it:
[`ro-crate-metadata.json`](example/ro-crate-metadata.json), a
[Process Run Crate](report.md#standards-based-provenance-the-process-run-crate)
describing every invocation below.

## The dataset

**airway** (GEO [GSE52778]): human airway smooth muscle cells from four donor
cell lines, treated with dexamethasone or untreated — 8 samples, 63,677
Ensembl genes. It is the canonical Bioconductor RNA-seq teaching dataset, so
every result here can be cross-checked against the DESeq2 vignette.
The counts come from the [airway] Bioconductor data package
(Himes et al. 2014, PMID 24926665).

[GSE52778]: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778
[airway]: https://bioconductor.org/packages/airway/

Everything below is scripted in
[`examples/airway/`](https://github.com/BU-Neuromics/de_toolkit/tree/main/examples/airway)
— `./run.sh` reproduces the report from scratch.

## The pipeline

**1. Look at the raw counts.** Summary statistics — distributions, zero
fractions, entropy, PCA colored by treatment:

```bash
detk-stats summary --log --color-col=dex -o raw_summary_stats.csv counts.csv sample_info.csv
```

In the report's PCA you can already see samples separate by treatment along
one component and by cell line along another.

**2. Filter.** Keep genes detected in at least half the samples, and let the
report record exactly what the rule removed:

```bash
detk-filter 'nonzero(all) >= 0.5' -o counts_filtered.csv counts.csv
```

**3. Normalize** with the DESeq2 median-of-ratios method (pure Python — no R
needed for this step), writing the size factors for the report:

```bash
detk-norm deseq2 -o norm_counts.csv --size-factors=size_factors.tsv counts_filtered.csv
```

**4. Variance-stabilize** (R/DESeq2), which the report documents with
before/after distributions and the mean-variance trend:

```bash
detk-transform vst -o vst_counts.csv counts_filtered.csv
```

**5. Flag entropy outliers**:

```bash
detk-outlier entropy counts_filtered.csv -p 0.05 -o entropy_flags.csv
```

**6. Differential expression.** The design formula uses detk's
[formula mini-language](formulas.md): cell line as a covariate, dexamethasone
treatment with `untrt` as the reference level:

```bash
detk-de deseq2 -o deseq2_results.csv "counts ~ cell + dex[untrt]" counts_filtered.csv sample_info.csv
```

The report renders this as a volcano + MA view with a model-term dropdown —
switch between the treatment effect (`dex__trt`) and the cell-line terms.

**7. Gene set enrichment** against [WikiPathways](https://www.wikipathways.org/)
(CC0-licensed GMT, Entrez-keyed — the script joins an Ensembl→Entrez mapping
onto the results first):

```bash
detk-enrich fgsea --filter-unannotated -i entrez -c 'dex__trt__log2FoldChange' \
    -o fgsea_results.csv wikipathways.gmt deseq2_results_entrez.csv
```

**8. Generate the report.** Every step above has been quietly writing its
JSON into `detk_report/json/`; one command renders it all:

```bash
detk-report generate
```

That's the [report you can open](example/detk_report.html) — one
self-contained file, offline forever, with the raw data behind every chart a
"Show data" click away, and the whole run described as standards-based
provenance in the crate next to it.

## Using a workflow manager

Each step is a plain command-line filter, so the pipeline drops directly into
Snakemake, Nextflow, or a shell script — see the
[Quickstart](quickstart.md#using-a-workflow-manager) for a Snakemake version
of this same shape.
