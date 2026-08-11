# airway example

Regenerates the published detk example report from the **airway** RNA-seq
dataset: human airway smooth muscle cells, dexamethasone-treated vs untreated
across four cell lines (8 samples).

- **Accession:** GEO [GSE52778](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778)
- **Citation:** Himes BE et al. *RNA-Seq transcriptome profiling identifies
  CRISPLD2 as a glucocorticoid responsive gene that modulates cytokine
  function in airway smooth muscle cells.* PLoS One 2014. PMID 24926665.
- **Counts source:** the [airway](https://bioconductor.org/packages/airway/)
  Bioconductor data package, which redistributes the published gene-level
  counts (Ensembl gene IDs).
- **Gene sets:** [WikiPathways](https://www.wikipathways.org/) GMT (CC0),
  downloaded at run time; WikiPathways GMTs are keyed by Entrez gene ID, so
  the run joins an Ensembl→Entrez mapping (org.Hs.eg.db) onto the DE results
  before enrichment.

## Requirements

- detk installed (`pip install de_toolkit` or `uv sync` in the repo root)
- R on `PATH` with `airway`, `org.Hs.eg.db`, `DESeq2`, `fgsea`, `jsonlite`,
  `data.table` — e.g. via bioconda:

```bash
mamba create -n detk-r -c conda-forge -c bioconda \
    r-base r-jsonlite r-data.table bioconductor-deseq2 bioconductor-fgsea \
    bioconductor-airway bioconductor-org.hs.eg.db
```

## Run

```bash
./run.sh              # full pipeline incl. fgsea (downloads the GMT)
./run.sh --skip-enrich  # no network needed
./run.sh --publish    # also copy report + crate into docs/example/
```

The pipeline: `detk-stats summary` → `detk-filter` → `detk-norm deseq2` →
`detk-transform vst` → `detk-outlier entropy` → `detk-de deseq2
"counts ~ cell + dex[untrt]"` → `detk-enrich fgsea` → `detk-report generate`.

Outputs land in this directory: the tabular results, `detk_report/detk_report.html`
(the self-contained report) and `ro-crate-metadata.json` (standards-based
provenance of the whole run). The published copy is served at
<https://bu-neuromics.github.io/de_toolkit/example/detk_report.html>.
