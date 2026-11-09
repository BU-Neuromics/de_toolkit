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
feature's length in kilobases, then by the sample's library size (the total
of its column of counts) in millions:

```text
FPKM[g, s] = count[g, s] / (length[g] / 1000) / (library_size[s] / 10^6)
           = count[g, s] * 10^9 / (length[g] * library_size[s])
library_size[s] = sum over g of count[g, s]
```

For example, a feature 2,000 bases long with 3 counts, in a sample whose
counts total 4, has FPKM 3 × 10^9 / (2000 × 4) = 375,000. FPKM is CPM divided
by the length in kilobases. A sample whose counts are all zero has no FPKM
values: its column is empty (NaN) and a warning is logged.

!!! note "Changed in 1.0"
    Before 1.0 (0.9.x), `fpkm` computed `count / (10^6 × length)`, without
    dividing by library size. Values from 1.0 on differ from 0.9.x output and
    are the documented FPKM.

detk must be given the length of every feature in the counts file, as a
two-column character-delimited file (format is sniffed) of feature identifier
and length in bases:

- every feature in the counts file must have an entry in the lengths file
- every length must be a positive number; a zero, negative, missing or
  non-numeric length is refused (reported as not a positive number)
- each feature may be listed only once; a lengths file that lists a feature
  twice is refused
- the lengths file may contain unused entries
- the two files do not need to be in the same order
- feature identifiers are read and matched as text, exactly as written:
  numeric identifiers (such as Entrez gene IDs) match, a zero-padded `007`
  matches only `007` (not `7`), and every identifier appears in the output as
  in the counts file
- an optional header line is allowed: the first line is skipped as a header
  only when its length field is text that is neither a number nor a
  missing-value token (empty, `NA`, `NaN`, `N/A`, `NULL`, `None`); otherwise it
  is read as a feature

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

`tpm` takes the same lengths file as [`fpkm`](#fpkm), with the same rules
(including the optional header line and the refusal of duplicated feature
identifiers, and the requirement that every length be a positive number).
The output has the same rows, in the same order, as the counts file. A sample
whose counts are all zero has no TPM (or CPM) values: its column is empty
(NaN) and a warning is logged.

```text
Usage:
    detk-norm tpm [options] <counts_fn> <lengths_fn>
```
