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
that column.

```text
Usage:
    detk-norm library [options] <counts_fn>
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
