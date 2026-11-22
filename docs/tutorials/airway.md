# Differential expression on airway

<!-- tutorial: requires R DESeq2 airway org.Hs.eg.db -->

This tutorial runs a complete differential expression analysis on a real,
public RNA-seq dataset: summary statistics, filtering, DESeq2 normalization,
a variance-stabilizing transform, outlier flags, DESeq2's test for the
treatment effect with the cell line as a covariate, gene symbols on the
results, and the report and provenance crate at the end. The report it
makes is detk's published example:

[open the finished example report](../example/detk_report.html) (one
self-contained HTML file: everything runs in your browser, nothing is sent
anywhere). The run's provenance is published next to it as
[`ro-crate-metadata.json`](../example/ro-crate-metadata.json).

It needs detk, and R with the Bioconductor packages DESeq2 (which detk runs
for the transform and the test), airway (the data) and org.Hs.eg.db (gene
symbols). With conda, for example:

```console
$ mamba create -n detk-r -c conda-forge -c bioconda \
    r-base r-jsonlite r-data.table bioconductor-deseq2 \
    bioconductor-airway bioconductor-org.hs.eg.db
```

## The data

**airway** (GEO [GSE52778]) is human airway smooth muscle cells from four
donor cell lines, each treated with dexamethasone (`trt`) or left untreated
(`untrt`): 8 samples, 63,677 Ensembl genes. It is Bioconductor's standard
RNA-seq teaching dataset, so every result here can be checked against the
DESeq2 vignette. The counts come from the [airway] Bioconductor data package,
which redistributes the published gene counts (Himes et al. 2014, PMID
24926665).

[GSE52778]: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778
[airway]: https://bioconductor.org/packages/airway/

detk reads plain delimited files, so the first step writes the package's
data out as three: the counts, the sample information, and a map from each
Ensembl gene ID to its Entrez ID and gene symbol (from org.Hs.eg.db). Save
this R script as `prepare_data.R` and run it:

```bash
cat > prepare_data.R <<'EOF'
suppressMessages({
    library(airway)
    library(org.Hs.eg.db)
})
data(airway)

# gene counts: Ensembl gene IDs x 8 samples
counts <- as.data.frame(assay(airway))
counts <- cbind(gene = rownames(counts), counts)
write.csv(counts, "counts.csv", row.names = FALSE, quote = FALSE)

# sample information: cell line and treatment
cd <- as.data.frame(colData(airway)[, c("cell", "dex")])
cd <- cbind(sample = rownames(cd), cd)
write.csv(cd, "sample_info.csv", row.names = FALSE, quote = FALSE)

# Ensembl gene ID -> Entrez ID and gene symbol (the first, where several)
ens <- rownames(assay(airway))
entrez <- mapIds(org.Hs.eg.db, keys = ens, column = "ENTREZID",
                 keytype = "ENSEMBL", multiVals = "first")
symbol <- mapIds(org.Hs.eg.db, keys = ens, column = "SYMBOL",
                 keytype = "ENSEMBL", multiVals = "first")
map <- data.frame(gene = ens, entrez = unname(entrez), symbol = unname(symbol))
write.csv(map, "gene_map.csv", row.names = FALSE, quote = FALSE)
EOF
Rscript prepare_data.R 2> /dev/null
cat sample_info.csv
```

<!-- tutorial: expect -->
```text
sample,cell,dex
SRR1039508,N61311,untrt
SRR1039509,N61311,trt
SRR1039512,N052611,untrt
SRR1039513,N052611,trt
SRR1039516,N080611,untrt
SRR1039517,N080611,trt
SRR1039520,N061011,untrt
SRR1039521,N061011,trt
```

Each cell line has one treated and one untreated sample, so the samples are
paired by cell line: the design below compares treated with untreated within
each cell line.

## Look at the raw counts

`detk-stats summary` computes the matrix's size, each sample's distribution
of counts, the zeros in each sample and each gene, each sample's entropy and
a principal component analysis. `--log` works on log counts, and
`--color-col=dex` colors the report's plots by treatment:

```bash
detk-stats summary --log --color-col=dex -o raw_summary_stats.csv counts.csv sample_info.csv
head -n 4 raw_summary_stats.csv
```

<!-- tutorial: expect -->
```text
#basestats
stat,val
num_cols,8
num_rows,63677
```

In the report's PCA the samples already separate by treatment along one
component and by cell line along another.

## Filter

Most of the 63,677 genes are not expressed in these cells. Keep the genes
with a nonzero count in at least half the samples; the report records what
the rule removed:

```bash
detk-filter 'nonzero(all) >= 0.5' -o counts_filtered.csv counts.csv
tail -n +2 counts_filtered.csv | wc -l
```

<!-- tutorial: expect -->
```text
24706
```

## Normalize

`detk-norm deseq2` divides each sample by its DESeq2 size factor, the median
ratio of its counts to each gene's geometric mean across the samples (in
Python: this step needs no R). `--size-factors` writes the factors to a
file, a header line and then a sample and its factor on each line:

```bash
detk-norm deseq2 -o norm_counts.csv --size-factors=size_factors.tsv counts_filtered.csv
cat size_factors.tsv
```

<!-- tutorial: expect -->
```text
sample	size_factor
SRR1039508	1.02364...
SRR1039509	0.89616...
SRR1039512	1.17948...
SRR1039513	0.67005...
SRR1039516	1.17767...
SRR1039517	1.39903...
SRR1039520	0.92077...
SRR1039521	0.94451...
```

These are the size factors DESeq2's own `estimateSizeFactors` finds for the
same counts. The normalized counts are for looking at and for methods that
take them; DESeq2's test below estimates the size factors itself, so it
takes the raw filtered counts, not `norm_counts.csv`.

## Variance-stabilize

Count variance grows with the mean, which lets the most expressed genes
dominate distances and plots. DESeq2's variance-stabilizing transform (VST)
removes that dependence; the report shows the distributions before and after
and the mean-variance trend:

```bash
detk-transform vst -o vst_counts.csv counts_filtered.csv
```

## Flag outliers

`detk-outlier entropy` computes each gene's entropy across the samples, which
is low for a gene whose counts come mostly from one or a few samples, and
flags the genes with an entropy below the percentile `-p` sets. Count the
flagged genes:

```bash
detk-outlier entropy counts_filtered.csv -p 0.05 -o entropy_flags.csv
head -n 3 entropy_flags.csv
grep -c ',True$' entropy_flags.csv
```

<!-- tutorial: expect -->
```text
gene,entropy,entropy_p0_05
ENSG00000000003,2.0222...,False
ENSG00000000419,2.0524...,False
925
```

The flags are for looking at, in the report's entropy plot: nothing below
removes the flagged genes.

## Differential expression

`detk-de deseq2` runs DESeq2 on the raw filtered counts with a design
written in detk's [formula mini-language](../formulas.md): the cell line as a
covariate, and the treatment with `untrt` as its reference level, so a
positive fold change is higher with dexamethasone:

```bash
detk-de deseq2 -o deseq2_results.csv "counts ~ cell + dex[untrt]" counts_filtered.csv sample_info.csv
head -n 1 deseq2_results.csv | tr , '\n' | grep dex
```

<!-- tutorial: expect -->
```text
dex__trt__log2FoldChange
dex__trt__lfcSE
dex__trt__stat
dex__trt__pvalue
dex__trt__padj
```

The results have a row per gene and, after its mean normalized count
(`baseMean`), five columns for each term of the design: the treatment's are
named `dex__trt__*`, and the `cell__*` columns hold the cell line terms. The
adjusted p-values (`padj`) are Benjamini-Hochberg over every gene in the
file, without the independent filtering DESeq2's `results()` adds by
default.

## Gene symbols

Ensembl IDs are hard to read. `detk-util annotate` adds the `symbol` column
of the map from the first step to the results, joining on the gene ID; a gene
with no symbol gets an empty one, and the command warns how many had none:

```bash
detk-util annotate --map-to=symbol -o deseq2_results_symbols.csv deseq2_results.csv gene_map.csv
```

Now a short table of the treatment's results, gene, symbol, fold change and
adjusted p-value, sorted by the adjusted p-value (the `awk` program finds the
columns by name in the header), and its first ten genes:

```bash
awk -F, -v OFS=, '
  NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
  { printf "%s,%s,%.3f,%.3g\n", $1, $col["symbol"],
      $col["dex__trt__log2FoldChange"], $col["dex__trt__padj"] }
' deseq2_results_symbols.csv | sort -t, -k4,4g > top_genes.csv
head -n 10 top_genes.csv
```

<!-- tutorial: expect -->
```text
ENSG00000152583,SPARCL1,4.575,9.52e-133
ENSG00000165995,CACNB2,3.291,2.84e-131
ENSG00000101347,SAMHD1,3.767,8.28e-125
ENSG00000120129,DUSP1,2.948,1.27e-124
ENSG00000189221,MAOA,3.354,3.12e-119
ENSG00000211445,GPX3,3.730,8.99e-108
ENSG00000157214,STEAP2,1.977,3.34e-100
ENSG00000162614,NEXN,2.036,4.05e-97
ENSG00000125148,MT2A,2.211,7.55e-92
ENSG00000154734,ADAMTS1,2.346,4.57e-86
```

All ten are higher with dexamethasone. They are the genes Bioconductor's
RNA-seq workflow finds at the top for this dataset with the same design;
DUSP1 and the metallothionein MT2A are well known glucocorticoid-induced
genes.

## The report and the crate

Every detk command above that has a report wrote its results into
`detk_report/` and rendered the report again, so the report is already up
to date. `detk-report generate` renders it from what is in the directory:

```bash
detk-report generate
ls detk_report
```

<!-- tutorial: expect -->
```text
detk_report.html
json
ro-crate-metadata.json
```

Open `detk_report/detk_report.html` in a browser: it is one self-contained
file, with a section for each step. The differential expression section is a
volcano and an MA plot with a menu of the design's terms: switch between the
treatment (`dex__trt`) and the cell lines. Next to the report, in the report
directory, detk wrote `ro-crate-metadata.json`, a
[Process Run Crate](../report.md#standards-based-provenance-the-process-run-crate)
that describes each step's command, its parameters and the files it read and
wrote. The steps it lists (the summary is listed as the six statistics it is
made of):

```bash
grep -o '"name": "detk-[^"]* run"' detk_report/ro-crate-metadata.json | sort -u
```

<!-- tutorial: expect -->
```text
"name": "detk-de deseq2 run"
"name": "detk-filter run"
"name": "detk-norm deseq2 run"
"name": "detk-outlier entropy run"
"name": "detk-stats basestats run"
"name": "detk-stats coldist run"
"name": "detk-stats colzero run"
"name": "detk-stats entropy run"
"name": "detk-stats pca run"
"name": "detk-stats rowzero run"
"name": "detk-transform vst run"
"name": "detk-util annotate run"
```

## Optional: gene set enrichment

This step downloads a gene set file, so the page shows it but its test does
not run it, and the published report does not have it. It needs the R
package fgsea as well (`bioconductor-fgsea`).

[WikiPathways](https://www.wikipathways.org/) publishes its human pathways
(CC0) as a GMT file keyed by Entrez gene ID; download the current one from
<https://data.wikipathways.org/current/gmt/>, the file named
`wikipathways-<date>-gmt-Homo_sapiens.gmt`, as `wikipathways.gmt`. The
results are keyed by Ensembl ID, so join the map's `entrez` column on first.
Several Ensembl genes can map to one Entrez ID and fgsea refuses an ID that
appears twice, so the join also keeps one row per Entrez ID (the first). It
needs pandas, which detk depends on, so run it with the Python detk is
installed in (the `python3` on `PATH` may lack pandas when detk was
installed with `uv tool install` or pipx):

```console
$ DETK_PY="$(dirname "$(command -v detk-de)")/python3"
$ [ -x "$DETK_PY" ] || DETK_PY=python3
$ "$DETK_PY" - <<'PY'
import pandas as pd
res = pd.read_csv("deseq2_results.csv")
gmap = pd.read_csv("gene_map.csv", dtype=str)
res = res.merge(gmap[["gene", "entrez"]], left_on=res.columns[0], right_on="gene", how="left")
res = res.dropna(subset=["entrez"]).drop_duplicates(subset=["entrez"])
res.to_csv("deseq2_results_entrez.csv", index=False)
PY
```

Then rank the genes by the treatment's fold change and test each pathway:

```console
$ detk-enrich fgsea --filter-unannotated -i entrez -c 'dex__trt__log2FoldChange' \
    -o fgsea_results.csv wikipathways.gmt deseq2_results_entrez.csv
```

`-c` names the ranking column; without it detk would rank by the last
numeric column, the treatment's adjusted p-value, which ranks by the wrong
quantity and in the wrong direction. The Wald statistic `dex__trt__stat` is
the other common choice. Run `detk-report generate` again to add the
enrichment to the report.

## Where next

- [Differential expression](../tools/de.md) has the options of
  `detk-de deseq2` and Firth's logistic regression, and
  [formulas](../formulas.md) the design mini-language.
- [The report](../report.md) says what each section shows and what the crate
  holds.
- The same pipeline drops into a workflow manager step for step: see the
  [quickstart](../quickstart.md#using-a-workflow-manager).
