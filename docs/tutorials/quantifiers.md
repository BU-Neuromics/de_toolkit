# From quantifier outputs to a normalized matrix

<!-- tutorial: requires cut awk grep sort -->

Most RNA-seq analyses start from a quantifier's output: one file per sample,
from salmon, kallisto, htseq-count or featureCounts. This tutorial takes
salmon's `quant.sf` files to a counts matrix, matches it to a sample sheet,
normalizes it to counts per million (CPM) and transcripts per million (TPM),
log-transforms it, summarizes it, and ends with detk's report and its
provenance crate. It needs detk and nothing else: no R.

## The data

The data are simulated, so you can share and change them freely: salmon
outputs for six samples of a small study, three `ctrl` and three `treat`,
over 300 made-up transcripts, plus P1, a pilot library that was quantified
with them but is not part of the study. The seeded script
[`simulate.py`](data/quantifiers/simulate.py) wrote them and writes the same
files byte for byte each time it runs. Make them in an empty directory with
the script, or copy them from a checkout of detk's repository, where they sit
next to it in `docs/tutorials/data/quantifiers/`:

```console
$ python simulate.py .
```

<!-- tutorial: hidden
```bash
cp -r "$TUTORIAL_SRC/data/quantifiers/salmon" "$TUTORIAL_SRC/data/quantifiers/samples.csv" .
```
-->

Salmon writes each sample to a directory of its own, and the file in each is
called `quant.sf`:

```bash
ls salmon
head -n 3 salmon/S1/quant.sf
```

<!-- tutorial: expect -->
```text
P1
S1
S2
S3
S4
S5
S6
Name	Length	EffectiveLength	TPM	NumReads
TX00001.2	1216	1029.500	2320.779735	124.000
TX00002.1	1577	1390.500	3782.946882	273.000
```

`NumReads` is salmon's estimate of the reads from each transcript. It is not
always a whole number, because salmon shares a read between the transcripts
it could have come from.

## Gather the counts into one matrix

`detk-util gather` reads every `quant.sf` and writes one matrix, a row per
transcript and a column per sample. It detects the format from the files'
header and takes the `NumReads` column. The files are all called `quant.sf`,
so each sample is named after its directory. Quote the pattern, and detk
expands it, taking the files in natural order:

```bash
detk-util gather -o counts.csv 'salmon/*/quant.sf'
head -n 4 counts.csv
```

<!-- tutorial: expect -->
```text
,P1,S1,S2,S3,S4,S5,S6
TX00001.2,105.420,124.000,106.000,319.000,147.000,93.000,130.412
TX00002.1,266.000,273.000,305.000,631.000,216.000,229.270,279.000
TX00003.1,572.707,546.000,365.096,924.000,332.000,442.000,429.000
```

The transcript IDs and the counts are kept as salmon wrote them, version
suffix (`.2`) and all; gather does not round the counts or add transcripts up
to genes. Every sample must list the same transcripts, or gather stops and
names the differences (`--on-mismatch` fills or drops them instead).

### Counts for differential expression

This tutorial stops at normalized tables, for which salmon's transcript
estimates are fine. Differential expression with `detk-de deseq2` wants raw
gene-level read counts, the kind featureCounts and htseq-count write, which
`detk-util gather` reads the same way. Gathered from salmon or kallisto and
passed to DESeq2, the estimates above rest on two assumptions:

- they are rounded to whole numbers, as if they were read counts;
- there is no sample-specific effective-length offset, which the standard
  tximport and DESeq2 route uses, so where fragment lengths or isoform usage
  differ between samples, fold changes can reflect length rather than
  expression.

To start a DE analysis from salmon or kallisto, summarize the transcripts to
genes with [tximport](https://bioconductor.org/packages/tximport/) instead,
with `countsFromAbundance = "lengthScaledTPM"`: gene counts scaled to each
gene's average transcript length, the form of its output that can be used as
a plain counts matrix. A short R script does it, given a transcript-to-gene
table (a CSV with a header line: transcript ID, gene ID):

```r
# Rscript tximport_counts.R salmon|kallisto TX2GENE OUT FILE...
args <- commandArgs(trailingOnly = TRUE)
files <- args[-(1:3)]
names(files) <- basename(dirname(files))  # one directory per sample
tx2gene <- read.csv(args[2])
txi <- tximport::tximport(files, type = args[1], tx2gene = tx2gene,
                          countsFromAbundance = "lengthScaledTPM",
                          dropInfReps = TRUE)
write.csv(txi$counts, args[3])
```

Run it through `detk-util record`, so the step, the script and the table are
in the report and the provenance crate like detk's own steps:

```console
$ version=$(Rscript -e "cat(format(packageVersion('tximport')))")
$ detk-util record --tool=tximport --tool-version="$version" \
    -i tximport_counts.R -i tx2gene.csv -o gene_counts.csv -- \
    Rscript tximport_counts.R salmon tx2gene.csv gene_counts.csv salmon/*/quant.sf
```

The [agent skill](../agent-skills.md) takes salmon and kallisto outputs the same
route.

## Match the counts to the sample sheet

The study's sample sheet has a row per sample and its condition. The pilot
library, P1, is not in it:

```bash
cat samples.csv
```

<!-- tutorial: expect -->
```text
sample,condition
S1,ctrl
S2,ctrl
S3,ctrl
S4,treat
S5,treat
S6,treat
```

`detk-util tidy` keeps the samples that are in both files, in the order of
the counts columns, so the counts lose P1. `-p` writes the sample sheet of
those samples too, with the same columns and header as `samples.csv`:

```bash
detk-util tidy -o counts_tidy.csv -p samples_tidy.csv counts.csv samples.csv
head -n 1 counts_tidy.csv
head -n 2 samples_tidy.csv
```

<!-- tutorial: expect -->
```text
,S1,S2,S3,S4,S5,S6
sample,condition
S1,ctrl
```

tidy logs how many samples it dropped from each file (`counts columns lost:
1`, `column data rows lost: 0`); check that they are the ones you meant to
leave out. Since detk 1.0.1, a command given a counts file and a sample sheet
whose samples differ exits 1 and names them rather than analysing the
samples the two share, so a subset like this one is always a step you take
with tidy. The steps below use the two tidied files.

## Counts per million

`detk-norm cpm` divides each sample's counts by its total and multiplies by
one million, so each sample's library size no longer matters:

```bash
detk-norm cpm -o cpm.csv counts_tidy.csv
```

Each column of `cpm.csv` now sums to one million. Add up S1's:

```bash
awk -F, 'NR > 1 { total += $2 } END { printf "%.3f\n", total }' cpm.csv
```

<!-- tutorial: expect -->
```text
1000000.000
```

## Transcripts per million

CPM does not allow for length: a long transcript gives more reads than a
short one at the same abundance. TPM divides each count by its transcript's
length in kilobases first, then scales each sample to one million.
`detk-norm tpm` takes the lengths from a file with a transcript's name and
length on each line. Salmon's `EffectiveLength`, the length less the
fragments that could not fit at its ends, is the one to use; take it from
any sample's `quant.sf` (the column header is skipped as a header):

```bash
cut -f 1,3 salmon/S1/quant.sf > lengths.tsv
detk-norm tpm -o tpm.csv counts_tidy.csv lengths.tsv
head -n 2 tpm.csv
```

<!-- tutorial: expect -->
```text
,S1,S2,S3,S4,S5,S6
TX00001.2,2320.7797353...,2052.8858193...,2599.2973373...,2121.6721760...,2000.4695925...,2651.0503475...
```

These are salmon's own TPM, which you saw in the first line of S1's
`quant.sf` (2320.779735). In this simulated study every sample has the same
effective lengths. In real data each sample's differ a little, with its
fragment lengths, so detk's TPM from one sample's lengths is close to
salmon's but not the same.

## Log-transform

Counts and their normalized values span orders of magnitude, so most plots
and many methods work on their logarithm. `detk-transform plog` takes the log
of each value plus a pseudocount, here log2(CPM + 1):

```bash
detk-transform plog -b 2 -o log2cpm.csv cpm.csv
```

## Summary statistics

`detk-stats summary` computes the matrix's size, the distribution of each
sample's values, the zeros in each sample and each transcript, each sample's
entropy and a principal component analysis. With the sample sheet it colors
the report's plots by condition:

```bash
detk-stats summary --color-col=condition -o summary.csv log2cpm.csv samples_tidy.csv
head -n 4 summary.csv
```

<!-- tutorial: expect -->
```text
#basestats
stat,val
num_cols,6
num_rows,300
```

## The report and the crate

Every detk command above that has a report wrote its results into
`detk_report/` and rendered the report again, so the report is already up
to date. `detk-report generate` renders it from what is in the directory,
for when you have removed or added module files by hand:

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
file, with a section for each step. Next to it, in the report directory,
detk wrote `ro-crate-metadata.json`, a
[Process Run Crate](../report.md#standards-based-provenance-the-process-run-crate)
that describes each step's command, its parameters and the files it read and
wrote, in terms any RO-Crate tool can read; it names each file by its path
from the report directory (`../counts.csv`). The steps it lists (the summary
is listed as the six statistics it is made of):

```bash
grep -o '"name": "detk-[^"]* run"' detk_report/ro-crate-metadata.json | sort -u
```

<!-- tutorial: expect -->
```text
"name": "detk-norm cpm run"
"name": "detk-norm tpm run"
"name": "detk-stats basestats run"
"name": "detk-stats coldist run"
"name": "detk-stats colzero run"
"name": "detk-stats entropy run"
"name": "detk-stats pca run"
"name": "detk-stats rowzero run"
"name": "detk-transform plog run"
"name": "detk-util gather run"
"name": "detk-util tidy run"
```

## Where next

- [`detk-util gather`](../tools/util.md) reads kallisto, htseq-count and
  featureCounts outputs the same way.
- [Normalization](../tools/norm.md) has DESeq2's size factors as well as CPM
  and TPM, and [transforms](../tools/transform.md) the variance-stabilizing
  ones.
- [The report](../report.md) says what each section shows and what the crate
  holds.
