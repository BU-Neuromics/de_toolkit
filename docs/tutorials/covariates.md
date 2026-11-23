# Derived covariates and recorded steps

<!-- tutorial: requires R DESeq2 airway -->
<!-- tutorial: requires mlr -->

A design often needs a covariate that is not in the sample sheet as it
stands: the log of a measurement, a measurement put on a standard scale, a
label shared by every sample. This tutorial derives three such columns from
the airway sample sheet with [Miller] (`mlr`), runs each step through
`detk-util record` so it becomes part of the analysis's provenance, shows
what happens when a value cannot be used, fits a DESeq2 design with one of
the derived columns, and then follows the column data `detk-de` read back
through the provenance crate to the Miller steps that made it.

It needs detk, R with the Bioconductor packages DESeq2 and airway, and
Miller 6. With conda, for example:

```console
$ mamba create -n detk-covariates -c conda-forge -c bioconda \
    r-base r-jsonlite r-data.table bioconductor-deseq2 \
    bioconductor-airway miller
```

[Miller]: https://miller.readthedocs.io

## Why formulas take column names only

In detk a [design formula](../formulas.md) names columns of the sample sheet
and nothing else: `counts ~ cell + dex` is a model, and detk does not
compute `log2(avgLength)` or a z-score inside one (DETK-0050). A formula
that computed its covariates would mix two jobs, saying what the model is
and making its data, and the second would be hidden inside the first: the
derived values would appear in no file you could look at, check or hand to
someone else, and a log of a zero or a missing value would surface, if at
all, as an error from deep inside the model fit. So a derived covariate is a
column of its own, in a sample sheet written by a step you can see, and the
formula names that column. The
[Miller recipes for derived covariates](../recipes/covariates.md) are tested
programs for the usual ones; this tutorial uses three of them.

## The data

**airway** (GEO [GSE52778]) is human airway smooth muscle cells from four
donor cell lines, each treated with dexamethasone (`trt`) or left untreated
(`untrt`): 8 samples, 63,677 Ensembl genes. The
[airway tutorial](airway.md) analyses it in full; here it is the counts and
a sample sheet that keeps one more column of the package's sample
information, `avgLength`, the mean length of each sample's sequenced reads.

[GSE52778]: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52778

Save this R script as `prepare_data.R`:

```bash
cat > prepare_data.R <<'EOF'
suppressMessages(library(airway))
data(airway)

# gene counts: Ensembl gene IDs x 8 samples
counts <- as.data.frame(assay(airway))
counts <- cbind(gene = rownames(counts), counts)
write.csv(counts, "counts.csv", row.names = FALSE, quote = FALSE)

# sample information: cell line, treatment and mean read length
cd <- as.data.frame(colData(airway)[, c("cell", "dex", "avgLength")])
cd <- cbind(sample = rownames(cd), cd)
write.csv(cd, "sample_info.csv", row.names = FALSE, quote = FALSE)
EOF
```

and run it through `detk-util record`, which runs the command after `--`,
checks that it wrote the files `-o` names, and writes a record of the step,
with the tool's version and a checksum of every file, into the report
directory (`detk_report/`). `-q` keeps `record`'s own messages to warnings
and errors:

```bash
detk-util record -q -o counts.csv -o sample_info.csv -- Rscript prepare_data.R
cat sample_info.csv
```

<!-- tutorial: expect -->
```text
sample,cell,dex,avgLength
SRR1039508,N61311,untrt,126
SRR1039509,N61311,trt,126
SRR1039512,N052611,untrt,126
SRR1039513,N052611,trt,87
SRR1039516,N080611,untrt,120
SRR1039517,N080611,trt,126
SRR1039520,N061011,untrt,101
SRR1039521,N061011,trt,98
```

The samples were sequenced to different read lengths, from 87 to 126 bases,
and not in step with the cell lines or the treatment. A technical difference
like that can shift counts, so the design below includes it as a covariate,
on a standard scale.

Most of the genes are not expressed in these cells; keep those with a
nonzero count in at least half the samples, as the airway tutorial does:

```bash
detk-filter 'nonzero(all) >= 0.5' -o counts_filtered.csv counts.csv
```

## A constant column

Each recipe is a Miller program and one `detk-util record` command that runs
it. The program writes the output file itself (`emit > @out`, or `tee` for
the constant column), so the same file name goes in Miller's
`-s out=...` and `record`'s `-o`. The first adds a column `study` that is
`airway` in every sample, a label that tells these samples apart once their
sheet is joined to another study's:

```bash
detk-util record -q -i sample_info.csv -o sample_info.study.csv -- \
  mlr --icsv --ocsv put -q -s out=sample_info.study.csv '$study = "airway"; tee > @out, $*' sample_info.csv
```

## The z-score

The z-score of `avgLength`, as `avgLength_zscore`: the read length less the
mean read length, over the sample standard deviation (n - 1). This is the
[z-score recipe](../recipes/covariates.md#z-score-centring-and-min-max) as
it is, with `-s col=avgLength`; it reads the sheet the constant column's
step wrote:

```bash
zscore='
  @rec[NR] = $*; @ids[NR] = $[[[1]]];
  if (!is_numeric($[@col])) { @bad[NR] = $[[[1]]] }
  else { @min = min(@min, $[@col]); @max = max(@max, $[@col]) }
  end {
    if (length(@rec) == 0) {
      eprint @col . "_zscore: " . @col . " has no values: the sheet has no samples";
      asserting_null("stop");
    }
    if (length(@bad) > 0) {
      eprint @col . "_zscore: " . @col . " is missing or not a number in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    if (@min == @max) {
      eprint @col . "_zscore: " . @col . " has the same value in every sample, " . joinv(@ids, ", ");
      asserting_null("stop");
    }
    n = length(@rec); sum = 0; ss = 0;
    for (i, r in @rec) { sum += r[@col] }
    mean = sum / n;
    for (i, r in @rec) { ss += (r[@col] - mean) ** 2 }
    sd = sqrt(ss / (n - 1));
    for (i, r in @rec) { @rec[i][@col . "_zscore"] = (r[@col] - mean) / sd }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.study.csv -o sample_info.zscore.csv -- \
  mlr --icsv --ocsv put -q -s col=avgLength -s out=sample_info.zscore.csv "$zscore" sample_info.study.csv
```

A coefficient for `avgLength_zscore` is the change in log2 expression per
standard deviation of read length, about 16 bases here, rather than per
base, and the column is centred on zero, so the intercept stays the
expression at the mean read length.

## The log

The [log base 2 recipe](../recipes/covariates.md#logarithms), as
`avgLength_log2`, on the sheet the z-score step wrote:

```bash
log2='
  @rec[NR] = $*;
  if (!is_numeric($[@col]) || $[@col] <= 0) { @bad[NR] = $[[[1]]] }
  end {
    if (length(@bad) > 0) {
      eprint @col . "_log2: " . @col . " is missing, not a number or not above 0 in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    for (i, r in @rec) { @rec[i][@col . "_log2"] = log(r[@col]) / log(2) }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.zscore.csv -o sample_info.covariates.csv -- \
  mlr --icsv --ocsv put -q -s col=avgLength -s out=sample_info.covariates.csv "$log2" sample_info.zscore.csv
cat sample_info.covariates.csv
```

<!-- tutorial: expect -->
```text
sample,cell,dex,avgLength,study,avgLength_zscore,avgLength_log2
SRR1039508,N61311,untrt,126,airway,0.7713495806621354,6.977279923499917
SRR1039509,N61311,trt,126,airway,0.7713495806621354,6.977279923499917
SRR1039512,N052611,untrt,126,airway,0.7713495806621354,6.977279923499917
SRR1039513,N052611,trt,87,airway,-1.6843756149152753,6.442943495848729
SRR1039516,N080611,untrt,120,airway,0.39354570441945685,6.906890595608519
SRR1039517,N080611,trt,126,airway,0.7713495806621354,6.977279923499917
SRR1039520,N061011,untrt,101,airway,-0.802833237015692,6.6582114827517955
SRR1039521,N061011,trt,98,airway,-0.9917351751370312,6.614709844115209
```

`sample_info.covariates.csv` has the three new columns after the sheet's
own, and every value Miller did not compute is as `prepare_data.R` wrote it.

## When a value cannot be used

A sample sheet is often put together by hand, and a value can go missing on
the way. Here is a copy of the sheet in which `SRR1039516`'s read length was
written as `NA`:

```bash
sed 's/^SRR1039516,N080611,untrt,120$/SRR1039516,N080611,untrt,NA/' sample_info.csv > sample_info_bad.csv
grep SRR1039516 sample_info_bad.csv
```

<!-- tutorial: expect -->
```text
SRR1039516,N080611,untrt,NA
```

The log recipe checks every sample before it computes anything, names the
sample it cannot use and stops; `detk-util record` then stops too, with exit
status 1, and records nothing:

<!-- tutorial: fails -->
```bash
detk-util record -q -i sample_info_bad.csv -o sample_info_bad.log2.csv -- \
  mlr --icsv --ocsv put -q -s col=avgLength -s out=sample_info_bad.log2.csv "$log2" sample_info_bad.csv
```

<!-- tutorial: expect -->
```text
avgLength_log2: avgLength is missing, not a number or not above 0 in SRR1039516
mlr: is_null type-assertion failed at NR=8 FNR=8 FILENAME=sample_info_bad.csv
detk-util: error: command failed with exit status 1: mlr --icsv --ocsv put -q -s col=avgLength -s out=sample_info_bad.log2.csv '...' sample_info_bad.csv (--verbose for the traceback)
```

The first line is the recipe's, the second Miller's, from the assertion that
stops it, and the last `detk-util record`'s. There is no output file, so no
later step can read a half-made sheet:

```bash
ls sample_info_bad*
```

<!-- tutorial: expect -->
```text
sample_info_bad.csv
```

Without the check, Miller would have written the text `(error)` as
`SRR1039516`'s `avgLength_log2` and exited 0, and a model given that column
would have read it as a category, or failed far from the cause.

## The design

`detk-de deseq2` fits the cell line, the z-scored read length and the
treatment, with `untrt` as the treatment's reference level, on the filtered
counts and the derived sheet. The formula names `avgLength_zscore` as it
would any column:

```bash
detk-de deseq2 -o deseq2_results.csv "counts ~ cell + avgLength_zscore + dex[untrt]" \
  counts_filtered.csv sample_info.covariates.csv
head -n 1 deseq2_results.csv | tr , '\n' | grep -e avgLength -e dex
```

<!-- tutorial: expect -->
```text
avgLength_zscore__log2FoldChange
avgLength_zscore__lfcSE
avgLength_zscore__stat
avgLength_zscore__pvalue
avgLength_zscore__padj
dex__trt__log2FoldChange
dex__trt__lfcSE
dex__trt__stat
dex__trt__pvalue
dex__trt__padj
```

A numeric covariate has one coefficient, named after its column; a factor
has one per level but the reference, named `variable__level`. The read
length's columns say, for each gene, how much its expression changes with
read length once the cell line and the treatment are accounted for, and the
treatment's are now adjusted for read length.

A formula that tries to compute the covariate itself is an error, which
says where the derived column should come from:

<!-- tutorial: fails -->
```bash
detk-de deseq2 -q -o deseq2_log2.csv "counts ~ cell + log2(avgLength) + dex[untrt]" \
  counts_filtered.csv sample_info.csv
```

<!-- tutorial: expect -->
```text
usage: detk-de deseq2 [options] <design> <counts_fn> <cov_fn>
detk-de deseq2: error: Invalid design: Formulas take column names only: log2(avgLength) is not a column of the column data file and looks like a call. Add the derived column to the column data file and name it in the formula; for recipes that derive a log, z-score or other column with Miller, see https://bu-neuromics.github.io/de_toolkit/recipes/covariates/
Run 'detk-de deseq2 --help' for help.
```

(`-q` keeps detk's progress messages off stderr, so only the error shows.)

## The steps in the crate

Every `detk-util record` that succeeded, and every detk command, wrote a
record of itself into `detk_report/json/`. `detk-report generate` renders
the report from them and writes the provenance crate,
`detk_report/ro-crate-metadata.json`, a
[Process Run Crate](../report.md#standards-based-provenance-the-process-run-crate):

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

In the crate each step is a `CreateAction` with the files it read
(`object`), the files it wrote (`result`) and the software that ran it
(`instrument`). For a recorded step the instrument is the external tool,
with the version `record` read from it (the first line of `mlr --version`),
since that is the software that made the files. Miller's entry:

```bash
grep -B 2 -A 1 '"name": "mlr"' detk_report/ro-crate-metadata.json
```

<!-- tutorial: expect -->
```text
      "@id": "#tool-mlr-mlr%206...",
      "@type": "SoftwareApplication",
      "name": "mlr",
      "softwareVersion": "mlr 6..."
```

A file one step writes and another reads is one entity in the crate, so the
crate holds the chain from each file back to where it came from, and a file
a recorded step read or wrote carries the SHA-256 checksum `record` took of
it. This Python program, which needs nothing but Python, starts from the
files the `detk-de deseq2` step read and follows each back, step by step,
printing the tool and version that made it, and whether the file still
matches its recorded checksum:

```bash
cat > trace.py <<'EOF'
import hashlib
import json

CRATE = "detk_report/ro-crate-metadata.json"
graph = json.load(open(CRATE))["@graph"]
ents = {e["@id"]: e for e in graph}
actions = [e for e in graph if e["@type"] == "CreateAction"]


def made_by(file_id):
    return next((a for a in actions if {"@id": file_id} in a.get("result", [])), None)


def checksum(file_id):
    recorded = ents[file_id].get("sha256")
    if recorded is None:
        return ""
    # file IDs are relative to the report directory, detk_report/
    with open("detk_report/" + file_id, "rb") as f:
        now = hashlib.sha256(f.read()).hexdigest()
    return ", sha256 matches" if now == recorded else ", sha256 DIFFERS"


def trace(file_id, depth=0):
    step = made_by(file_id)
    name = ents[file_id]["name"]
    if step is None:
        print(f"{'  ' * depth}{name}: no recorded step made it")
        return
    tool = ents[step["instrument"]["@id"]]
    print(f"{'  ' * depth}{name} <- {tool['name']} ({tool['softwareVersion']}){checksum(file_id)}")
    for obj in step.get("object", []):
        if ents[obj["@id"]]["@type"] == "File":
            trace(obj["@id"], depth + 1)


de = next(a for a in actions if a["name"] == "detk-de deseq2 run")
for obj in de["object"]:
    if ents[obj["@id"]]["@type"] == "File":
        trace(obj["@id"])
EOF
python3 trace.py
```

<!-- tutorial: expect -->
```text
counts_filtered.csv <- detk-filter (...)
  counts.csv <- Rscript (Rscript (R) version ...), sha256 matches
sample_info.covariates.csv <- mlr (mlr 6...), sha256 matches
  sample_info.zscore.csv <- mlr (mlr 6...), sha256 matches
    sample_info.study.csv <- mlr (mlr 6...), sha256 matches
      sample_info.csv <- Rscript (Rscript (R) version ...), sha256 matches
```

The sheet `detk-de` read, `sample_info.covariates.csv`, was made by Miller,
with its version, from the sheet the z-score step made, which Miller made
from the constant column's sheet, which Miller made from the sheet R wrote;
the counts go back through `detk-filter` to R as well. The failed step is
not there: `record` writes nothing for a step that fails. (`detk-filter`
reads and writes its files itself, so its output has no checksum of
`record`'s.)

The HTML report, `detk_report/detk_report.html`, lists each recorded step as
"Recorded external step", with its command, tool, version and files.

## Where next

- [Derived covariates with Miller](../recipes/covariates.md) has the other
  recipes (log base 10, natural log, a log with a pseudocount, centring and
  min-max) and what each checks.
- [Formulas](../formulas.md) is detk's design mini-language, and
  [`detk-util record`](../tools/util.md#record) what `record` checks and
  records.
- The [airway tutorial](airway.md) is the full analysis of the same data,
  from summary statistics to gene symbols and the report.
