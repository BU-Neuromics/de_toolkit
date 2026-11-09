---
name: detk
description: Run a bulk RNA-seq differential expression analysis with de_toolkit (detk), a suite of command line tools for count matrices. Use when given per-sample quantifier outputs (salmon, kallisto, htseq-count, featureCounts) or a counts matrix (genes x samples), and a sample information table, and asked to build a counts matrix, filter, normalize (DESeq2, CPM, TPM, FPKM, library size), test for differential expression (DESeq2 or Firth logistic regression), add gene symbols to results, run gene set enrichment (fgsea), or produce a self-contained HTML report with provenance. Covers installing detk and its R/Bioconductor dependencies.
---

# detk: count matrix analysis from the command line

de_toolkit (`detk`) is a set of command line tools for counts matrices from
high-throughput sequencing: summary statistics, filtering, normalization,
transformation, differential expression and gene set enrichment. Every tool
reads and writes plain delimited text, so you drive an analysis with a short
sequence of shell commands. Each command also records a JSON document under
`./detk_report/json/`, and `detk-report generate` renders all of them into one
self-contained HTML report plus a provenance file (`ro-crate-metadata.json`).

The command line is detk's stable interface. Do not import `de_toolkit` in
Python to do what a command does.

Documentation: https://bu-neuromics.github.io/de_toolkit/

## 1. Install

detk needs Python 3.11 or newer.

```bash
pip install 'de_toolkit>=1.0'        # or: uv tool install 'de_toolkit>=1.0'
```

If pip finds no version 1.0 or newer, install from GitHub instead:

```bash
pip install git+https://github.com/BU-Neuromics/de_toolkit.git
# or: uv tool install git+https://github.com/BU-Neuromics/de_toolkit.git
```

Never install a plain `de_toolkit` without the version bound: PyPI's old 0.9.12
release cannot run on Python 3.10 or newer. Its sign is that every command dies
on start with `ImportError: cannot import name 'Mapping' from 'collections'`.
If you see that error, reinstall from GitHub as above; do not downgrade Python
or patch the installed package. (`--version` cannot tell the two apart: until
1.0 is released the GitHub build also reports 0.9.12.)

`detk-de`, `detk-enrich`, and `detk-transform rlog`/`vst` call R. They need R
(`Rscript` on `PATH`) with these packages:

- DESeq2 (Bioconductor): `detk-de deseq2`, `detk-transform rlog`, `detk-transform vst`
- fgsea (Bioconductor): `detk-enrich fgsea`
- logistf (CRAN): `detk-de firth`
- jsonlite (CRAN): the R bridge itself

```r
install.packages(c("BiocManager", "logistf", "jsonlite"))
BiocManager::install(c("DESeq2", "fgsea"))
```

or with conda/mamba:

```bash
mamba install -c conda-forge -c bioconda \
    r-base r-jsonlite r-logistf bioconductor-deseq2 bioconductor-fgsea
```

Check the R bridge before running the R-backed steps:

```bash
detk-wrapr check
```

`detk-stats`, `detk-filter`, `detk-norm`, `detk-outlier`, `detk-util` (including
`gather` and `annotate`) and `detk-report` work without R. If
R is missing and the user cannot install it, run those steps and say which
steps were skipped and why.

## 2. Inputs

Two comma, tab or otherwise delimited files (detk sniffs the delimiter; it
writes commas unless given `-d CHAR`):

- **counts matrix**: first column holds unique feature IDs (e.g. Ensembl gene
  IDs), every other column is one sample, values are raw integer counts.
- **sample info** (column data): first column holds sample names that match
  the counts column names; the other columns are covariates (condition,
  batch, cell line, ...).

Feature IDs and sample names are read as text exactly as written, so a
zero-padded ID such as `007` stays `007`, and a sample named `001` stays
`001`, through every detk command, the R-backed ones (`detk-de`,
`detk-transform vst` and `rlog`) and `detk-enrich fgsea` included. Two IDs
that differ only as text (`1.10` and `1.1`) stay distinct. The R-backed
commands stop on a counts file that lists the same ID twice; the Python
commands do not check, so look for duplicate IDs before running them.

### Starting from quantifier outputs

If the user has one output file per sample from a quantifier rather than a
counts matrix, build the matrix with `detk-util gather`. It reads salmon
(`quant.sf`, `quant.genes.sf`), kallisto (`abundance.tsv`), htseq-count and
featureCounts outputs, detects the format from each file's header, and takes
each format's count column (salmon `NumReads`, kallisto `est_counts`):

```bash
detk-util gather -o counts.csv salmon/*/quant.genes.sf
detk-util gather --name-from='([^/]+)_quant/' -o counts.csv 'quant/*_quant/quant.sf'
detk-util gather -o counts.csv htseq/*.counts
detk-util gather -o counts.csv featurecounts.txt
```

- Sample names come from the file names without their last extension, or,
  when those are not unique (several `quant.sf` or `abundance.tsv`), from
  each file's directory, for every file of the run (a single `quant.sf` is
  named `quant`; use `--name-from` for names that do not depend on the other
  files). The second line above names `quant/A_quant/quant.sf` `A` rather
  than `A_quant`. A quoted pattern is expanded by gather, in
  natural order (`s2` before `s10`). Pass `--name-from=REGEX` (its first
  group is the name) when the default does not give the names used in the
  sample info, and check the header of `counts.csv` against the sample info
  before going on.
- In featureCounts output each count column is a sample, named from the BAM
  path in its header; one file can hold every sample.
- gather extracts the column as written and does not aggregate transcripts
  to genes. salmon `quant.sf` and kallisto `abundance.tsv` are per
  transcript: for a gene-level analysis, gather salmon's `quant.genes.sf`
  (written when salmon is given a transcript-to-gene map) or ask the user
  how to summarize to genes.
- Every sample must list the same features, or gather stops and names the
  differences; `--on-mismatch=fill` (absent features get 0) or
  `--on-mismatch=drop` (keep the features all samples share) go on. Ask the
  user before choosing one, since a mismatch often means files from
  different annotations.
- htseq-count's summary lines (`__no_feature`, ...) are left out of the
  matrix and recorded in the report.
- salmon and kallisto counts are estimates with fractions; `detk-de deseq2`
  rounds them, so they can go to it as they are.

### Check the two files

Look at both files first (`head`). Confirm the sample names agree. If the two
files hold different or differently ordered samples, tidy them:

```bash
detk-util tidy -o counts_tidy.csv -p sample_info_tidy.csv counts.csv sample_info.csv
```

Ask the user which covariate is the condition of interest and which level is
the reference (for example untreated, control) if the request does not say.

## 3. The analysis

Run the steps in order, from the directory where the report should go. Every
command writes its table with `-o FILE` (stdout otherwise) and logs to
stderr. Keep the default report directory (`./detk_report`) unless the user
wants another one, and then pass the same `--report-dir=DIR` to every step.

**Summary statistics** on the raw counts (optional, recommended): distributions,
zeros, entropy and PCA, colored by a covariate:

```bash
detk-stats summary --log --color-col=condition -o raw_summary_stats.csv counts.csv sample_info.csv
```

**Filter** lowly detected genes. The filter expression describes the rows to
**keep**. Keeping genes with a nonzero count in at least half the samples is a
sound default:

```bash
detk-filter 'nonzero(all) >= 0.5' -o counts_filtered.csv counts.csv
```

Other forms: `'mean(all) > 10'`, `'mean(all) > 10 and zero(all) < 0.5'`, and,
with the sample info as a third argument, per-group rules such as
`'nonzero(condition) > 0.5'` (kept if any group passes) or, for one group
only, `'nonzero(condition[treated]) >= 0.5'`. Always quote the expression.

For `zero` and `nonzero`, a threshold strictly between 0 and 1 is a
**fraction** of samples, and 0 or anything of 1 or more is a **count** of
samples. So `nonzero(all) >= 1` keeps genes nonzero in at least one sample,
not in every sample; to require every sample, give the number of samples
(`nonzero(all) >= 8` for eight samples). Column names used in an expression
must be at least two characters long.

**Normalize** with the DESeq2 median-of-ratios method (pure Python). The size
factors go into the report; no separate file is needed:

```bash
detk-norm deseq2 -o norm_counts.csv counts_filtered.csv
```

`detk-norm` has five methods; pick by what the values are for:

- `detk-norm deseq2`: the default for comparing a gene across samples
  (clustering, PCA, heatmaps, Firth regression). Its size factors are robust
  to a few very highly expressed genes changing between conditions.
- `detk-norm cpm`: counts per million, each sample divided by its total
  count and multiplied by 1e6. Simple and widely understood; use it for
  expression thresholds and plots, or when the user asks for CPM. Unlike
  deseq2 it is skewed when a few genes take up much of a library.
- `detk-norm library`: the same scaling as cpm without the factor of 1e6,
  so each sample sums to 1 (proportions of the library). Use it when the
  next tool wants proportions.
- `detk-norm tpm`: transcripts per million, each count divided by its
  feature's length in kilobases and each sample then scaled to sum to 1e6.
  Use it to compare genes within a sample, or when the user asks for TPM.
  Needs a lengths file:

  ```bash
  detk-norm tpm -o tpm.csv counts_filtered.csv lengths.csv
  ```

- `detk-norm fpkm`: fragments per kilobase per million,
  `count * 1e9 / (length * library size)`, from the same lengths file.
  Prefer TPM unless FPKM is asked for. FPKM values from detk 1.0 differ
  from 0.9.x, which never divided by library size; this is a correction, so
  do not compare them with FPKM from an older detk.

The lengths file has two columns: the feature ID as written in the counts
file and its (effective) length in bases; an optional header line is
skipped. Every feature in the counts must be listed, once, with a positive
length, or the command stops. featureCounts output carries a `Length`
column to build it from; for salmon or kallisto, take `Name` and `Length`
(or `EffectiveLength`) from one sample's file. Ask the user for one rather
than guessing lengths.

Normalized values of any method are for inspection, plots and clustering.
**Do not pass normalized counts to `detk-de deseq2`**, which expects raw
counts and normalizes internally.

**Differential expression** with DESeq2, on the filtered raw counts:

```bash
detk-de deseq2 -o deseq2_results.csv "counts ~ condition[control]" counts_filtered.csv sample_info.csv
```

The design uses detk's formula mini-language:

- `counts` must be the only term on the left hand side for DESeq2.
- Name the reference level in brackets: `condition[control]`.
- Add covariates on the right: `"counts ~ batch + condition[control]"`.
- Output columns are named `<term>__<level>__<statistic>`, for example
  `condition__treated__log2FoldChange`, `__lfcSE`, `__stat`, `__pvalue`,
  `__padj`, for every term in the model (`--last-term-only` for DESeq2's
  default of the last term only). The first column holds the feature IDs.
- No Cook's distance filtering or independent filtering is done, so filter
  beforehand.

For two classes with many replicates (about ten or more per class), Firth
logistic regression puts `counts` on the right and the class on the left, and
takes normalized counts:

```bash
detk-de firth -o firth_results.csv "condition[control] ~ counts" norm_counts.csv sample_info.csv
```

Firth output has a `status` column and, for each model term, the columns
`<term>__beta`, `<term>__p` and `<term>__padj`; the term of interest is
`counts` (`counts__beta`, `counts__padj`).

**Gene set enrichment** with fgsea, ranking genes by a statistic column of the
DE results against a GMT file of gene sets:

```bash
detk-enrich fgsea -i gene -c condition__treated__log2FoldChange -o fgsea_results.csv gene_sets.gmt deseq2_results.csv
```

- `-i` is the column holding feature IDs (default: the first column) and `-c`
  the column whose values rank the genes, highest first. Always pass `-c`
  with the full output column name from the DE results: without it detk
  ranks by the last numeric column, which in DESeq2 output is the last
  term's `__padj`, so the ranking would be by the wrong quantity and in the
  wrong direction.
- This example, like detk's published airway example, ranks by
  `__log2FoldChange`. The Wald statistic (`__stat`) is the other common
  choice; it down-weights noisy low-count genes that unshrunk fold changes
  put at the extremes. Say which column you ranked by.
- The IDs in the GMT and in the results must be from the same system. Most
  GMTs (MSigDB, WikiPathways) use gene symbols or Entrez IDs, while counts are
  often keyed by Ensembl IDs. If they differ, map the IDs onto the results
  table first, with `detk-util annotate --drop-unmapped` (below) or a small
  pandas or R join, and say which mapping you used. fgsea refuses an ID
  that appears twice, so when several genes map to one ID keep one row per
  ID (the airway example shows the join); an ID that maps to several values
  gets them joined with `;` by annotate, which matches nothing in a GMT.
- `detk-enrich fgsea --filter-unannotated` drops genes absent from every gene
  set.
- Ask the user for the gene set collection if none is given; do not invent
  one.

**Gene symbols.** DE results keyed by Ensembl or other IDs are hard to read.
Add symbols, or any other feature metadata, from a mapping table whose first
column holds the result IDs:

```bash
detk-util annotate --map-to=symbol -o deseq2_results_annotated.csv deseq2_results.csv gene_map.csv
```

- The result keeps its rows and order; the added columns come last. An
  unmapped ID gets empty columns (`--drop-unmapped` drops the row), and an ID
  with several mapping rows gets the values joined with `;`.
- `--map-from=COL` names the mapping column to join on (default the first),
  `--map-to=COLS` the columns to add (default all others), and `-i` the ID
  column of the result (default the first).
- `--strip-versions` drops Ensembl version suffixes (`ENSG00000000003.15`)
  on both sides before joining.
- detk does not ship a mapping. Ask the user for one, or build it from the
  annotation used for quantification (a GTF, or Bioconductor's
  `org.*.eg.db` as in the airway example). Report how many IDs went
  unmapped; detk logs it and records it in the report.

**Report.** Render every step recorded so far:

```bash
detk-report generate
```

This writes `detk_report/detk_report.html` (self-contained, works offline) and
`ro-crate-metadata.json` (Process Run Crate provenance of every invocation).
The crate is written in the directory where `detk-report generate` runs, not
under `detk_report/`.
Re-running a command with the same parameters replaces its entry rather than
duplicating it. `detk-report clean` deletes the report directory to start over.

## 4. Report back

Tell the user: the commands run, how many genes the filter kept (detk logs
`features kept after filtering`), the number of genes at `padj < 0.05` for the
term of interest (DESeq2: `<term>__<level>__padj`; Firth: `<term>__padj`), the top enriched gene sets, and the paths to the result
tables (the annotated one if you added symbols), the HTML report and the
provenance crate. State any step skipped and
why.

## Worked example and reference

- [references/airway.md](references/airway.md): the full pipeline on the
  public airway dataset (dexamethasone vs untreated, four cell lines), the
  example detk's own documentation uses. It starts from a counts matrix
  taken from the airway Bioconductor package, so it does not use
  `detk-util gather`.
- [references/commands.md](references/commands.md): the usage of every command
  above. `<command> <subcommand> --help` prints the authoritative usage for
  the installed version; check it when in doubt rather than guessing an
  option.
