# Worked example: the airway dataset

The airway dataset (GEO GSE52778; Himes et al. 2014, PMID 24926665): human
airway smooth muscle cells from four donor cell lines, treated with
dexamethasone (`trt`) or untreated (`untrt`); 8 samples, 63,677 Ensembl
genes. detk's documentation runs this same pipeline:
https://bu-neuromics.github.io/de_toolkit/example/ (script:
`examples/airway/run.sh` in the de_toolkit repository).

Use it to check that an installation works end to end, or as the template for
a two-condition design with a blocking covariate.

## Requirements

detk installed, and R with `airway`, `org.Hs.eg.db`, `DESeq2`, `fgsea`,
`jsonlite` and `data.table`, for example:

```bash
mamba create -n detk-r -c conda-forge -c bioconda \
    r-base r-jsonlite r-data.table bioconductor-deseq2 bioconductor-fgsea \
    bioconductor-airway bioconductor-org.hs.eg.db
```

## 1. Get the data

Write the counts, the sample info and an Ensembl to Entrez map from the
airway Bioconductor package (save as `prepare_data.R`, run with
`Rscript prepare_data.R`):

```r
suppressMessages({
    library(airway)
    library(org.Hs.eg.db)
})
data(airway)

counts <- as.data.frame(assay(airway))
counts <- cbind(gene = rownames(counts), counts)
write.csv(counts, "counts.csv", row.names = FALSE, quote = FALSE)

cd <- as.data.frame(colData(airway)[, c("cell", "dex")])
cd <- cbind(sample = rownames(cd), cd)
write.csv(cd, "sample_info.csv", row.names = FALSE, quote = FALSE)

ens <- rownames(assay(airway))
entrez <- mapIds(org.Hs.eg.db, keys = ens, column = "ENTREZID",
                 keytype = "ENSEMBL", multiVals = "first")
symbol <- mapIds(org.Hs.eg.db, keys = ens, column = "SYMBOL",
                 keytype = "ENSEMBL", multiVals = "first")
map <- data.frame(gene = ens, entrez = unname(entrez), symbol = unname(symbol))
write.csv(map, "gene_map.csv", row.names = FALSE, quote = FALSE)
```

`sample_info.csv` has the columns `sample`, `cell` (four cell lines) and
`dex` (`trt` or `untrt`).

## 2. Run detk

```bash
# raw count statistics, PCA colored by treatment
detk-stats summary --log --color-col=dex -o raw_summary_stats.csv counts.csv sample_info.csv

# keep genes with nonzero counts in at least half the samples
detk-filter 'nonzero(all) >= 0.5' -o counts_filtered.csv counts.csv

# DESeq2 median-of-ratios normalization, with size factors for the report
detk-norm deseq2 -o norm_counts.csv --size-factors=size_factors.tsv counts_filtered.csv

# optional: variance-stabilizing transform and entropy outlier flags
detk-transform vst -o vst_counts.csv counts_filtered.csv
detk-outlier entropy counts_filtered.csv -p 0.05 -o entropy_flags.csv

# DESeq2 on raw filtered counts: cell line as a covariate, untreated as reference
detk-de deseq2 -o deseq2_results.csv "counts ~ cell + dex[untrt]" counts_filtered.csv sample_info.csv
```

The filter keeps about 24,700 of the 63,677 genes. The treatment effect is in
the `dex__trt__*` columns of `deseq2_results.csv`
(`dex__trt__log2FoldChange`, `dex__trt__padj`, ...); the `cell__*` columns
hold the cell line terms.

## 3. Gene set enrichment

WikiPathways GMT files are keyed by Entrez gene ID, the results by Ensembl
ID, so join the map onto the results first:

```bash
python - <<'PY'
import pandas as pd
res = pd.read_csv("deseq2_results.csv")
gmap = pd.read_csv("gene_map.csv", dtype=str)
res = res.merge(gmap[["gene", "entrez"]], left_on=res.columns[0], right_on="gene", how="left")
res = res.dropna(subset=["entrez"]).drop_duplicates(subset=["entrez"])
res.to_csv("deseq2_results_entrez.csv", index=False)
PY
```

Download the current human WikiPathways GMT (CC0) from
https://data.wikipathways.org/current/gmt/ (the file named
`wikipathways-<date>-gmt-Homo_sapiens.gmt`) as `wikipathways.gmt`, then:

```bash
detk-enrich fgsea --filter-unannotated -i entrez -c 'dex__trt__log2FoldChange' \
    -o fgsea_results.csv wikipathways.gmt deseq2_results_entrez.csv
```

Without network access, skip this step and say so.

## 4. Report

```bash
detk-report generate
```

Open `detk_report/detk_report.html`. Compare it with the published report at
https://bu-neuromics.github.io/de_toolkit/example/detk_report.html: samples
separate by treatment on one principal component and by cell line on
another, and the volcano plot's term menu switches between `dex__trt` and the
cell line terms.
