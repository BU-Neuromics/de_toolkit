# `norm` — normalizing count matrices

Count normalization strategies. None of these subcommands require R — the
DESeq2 procedure is a Python port.

## `deseq2`

Normalize using the median-of-ratios method as implemented in the R package
[DESeq2]: each sample is divided by a size factor calculated as the median
ratio of each gene count to the geometric mean count across all samples.

```text
Usage:
    detk-norm deseq2 [options] <counts_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
    --size-factors=FILE          Write out the size factors found by the DESeq2
                                 method to two column tab separated file where
                                 the first column is sample name and the second
                                 column is the size factor
```

The implementation is roughly equivalent to the following R:

```r
library(DESeq2)

counts <- as.matrix(read.table(counts.fn, row.names=1))
colData <- data.frame(name=seq(ncol(counts)))

dds <- DESeqDataSetFromMatrix(
    countData=counts,
    colData=colData,
    design = ~ 1
)

dds <- estimateSizeFactors(dds)
write.table(counts(dds, normalized=TRUE), norm.counts.fn)
```

[DESeq2]: https://bioconductor.org/packages/release/bioc/html/DESeq2.html

## `library`

Library size normalization: counts in each column are divided by the sum of
that column, so each column of the output sums to 1. Use [`cpm`](#cpm) for
the same values scaled to counts per million.

```text
Usage:
    detk-norm library [options] <counts_fn>
```

## `cpm`

Counts Per Million: counts in each column are divided by the sum of that
column and multiplied by one million, so each column of the output sums to
1,000,000. This is `library` scaled by 10^6. A sample with zero total counts
produces `NaN` values and a warning.

```text
Usage:
    detk-norm cpm [options] <counts_fn>
```

## `fpkm`

Fragments Per Kilobase per Million reads: each count is divided by the
feature's length in kilobases, then by the sample's total reads in millions.

detk must be given the length of every feature in the counts file, as a
two-column character-delimited file (format is sniffed) of feature identifier
and length in bases:

- every feature in the counts file must have an entry in the lengths file
- the lengths file may contain unused entries
- the two files do not need to be in the same order

```text
Usage:
    detk-norm fpkm [options] <counts_fn> <lengths_fn>
```

## `tpm`

Transcripts Per Million: each count is divided by the feature's length in
kilobases, giving a per-kilobase rate, and each column of rates is then
scaled to sum to 1,000,000:

```text
rate[g, s] = count[g, s] / (length[g] / 1000)
TPM[g, s]  = rate[g, s] / sum over g of rate[g, s] * 10^6
```

Unlike FPKM, TPM values sum to the same total in every sample, so the
proportion of a sample's transcripts a feature represents is comparable
across samples. When every feature has the same length, TPM equals CPM.

`tpm` takes the same lengths file as [`fpkm`](#fpkm), with the same rules;
in addition every length must be a positive number. A header line in the
lengths file is allowed (it is recognized by its second field not being a
number). The output has the same rows, in the same order, as the counts
file.

```text
Usage:
    detk-norm tpm [options] <counts_fn> <lengths_fn>
```
