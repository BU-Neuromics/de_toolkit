# `util` — counts, column data and result file utilities

Functions for tidying up counts and [column data](../concepts.md) files —
mostly subsetting one or the other so the sample IDs and their order match.
Combined with `csvgrep` from [csvkit], this is useful for extracting subsets
of samples for downstream differential expression analysis. `gather` builds
the counts matrix from per-sample quantifier outputs in the first place, and
`annotate` adds feature metadata, such as gene symbols, to a result table.

[csvkit]: https://csvkit.readthedocs.io

## `gather`

Combine per-sample outputs of [salmon] (`quant.sf`), [kallisto]
(`abundance.tsv`), [htseq-count] or [featureCounts] into one counts matrix,
with a row per feature and a column per sample, ready for every other detk
tool.

```text
Usage:
    detk-util gather [options] <files>...

Options:
    --format=FMT           salmon, kallisto, htseq, featurecounts or auto
                           [default: auto]
    --column=COL           Column to extract from each file, by name or 0-based
                           position (default: the format's count column)
    --name-from=REGEX      Regular expression deriving each sample name from
                           its file path (the first group, or the whole match)
    --on-mismatch=WHAT     What to do when the samples list different features:
                           error, fill (with 0) or drop [default: error]
    -o FILE --output=FILE  Destination of the counts matrix [default: stdout]
```

For a salmon run per sample in `sample_1__salmon/`, `sample_2__salmon/`, ...:

```bash
detk-util gather --name-from='(sample_[0-9]+)__salmon' -o raw_counts.csv \
    sample_*__salmon/quant.sf
```

**Formats.** With `--format=auto` (the default) each file's format is detected
from its first lines, never from its name: salmon and kallisto by their exact
header line, featureCounts by its `# Program:featureCounts` line or its
`Geneid Chr Start End Strand Length` header, and htseq-count by a first line
with no header whose fields after the ID are integers. Every file must have
the same format; a file that matches none of these is refused with a request
for `--format`.

**Columns.** One column is extracted from each file, as written:

| format          | default column              | other useful columns |
|-----------------|-----------------------------|----------------------|
| `salmon`        | `NumReads`                  | `TPM`                |
| `kallisto`      | `est_counts`                | `tpm`                |
| `htseq`         | the count column (`1`)      |                      |
| `featurecounts` | every count column          | one BAM's column     |

Pick another with `--column`, by header name or 0-based position.
htseq-count 0.13 and later, given several BAM files, writes one count column
per BAM and no header naming them; such a file is refused unless `--column`
picks one of its columns (`--column=2` for the second BAM), so that no sample
is lost silently. Run htseq-count once per sample to gather them all.

Feature IDs and values are kept exactly as written (`9.512` stays `9.512`,
`007` stays `007`). Every value must be a plain finite number as quantifiers
write them: digits with an optional sign, decimal fraction and exponent
(`42`, `9.512`, `1.5e-06`). Anything else, including `NA`, `nan`, `inf`,
padded values and digit separators (`1_000`, `1,000`), is an error, as is a
feature listed twice in one file. htseq-count's summary lines (`__no_feature`, `__ambiguous`, ...)
are not features: they are left out of the matrix and their values recorded
in the report. `gather` does no aggregation: transcript-level salmon or
kallisto output gives a transcript-level matrix.

**Sample names.** By default a sample is named after its file, without the
last extension (`s1.counts.txt` becomes `s1.counts`). When those names are not
unique among the files given, as with salmon's `quant.sf` and kallisto's
`abundance.tsv`, every sample is named after the directory holding its file
instead, all or nothing. A default name therefore depends on the other files
in the run: a single `s1/quant.sf` is named `quant`, but `s1` when gathered
with `s2/quant.sf`. Use `--name-from` for names that never change. With `--name-from`, the name is
the first group of the regular expression, or else its whole match, searched
in the path as given. In featureCounts output each count column is a sample,
named the same way from the column header (the BAM file's path), so
`bam/A.bam` becomes `A`. Two samples with the same name are an error.

**Order.** The samples are written in the order of the files on the command
line (featureCounts' columns in their order within the file). A quoted glob
that gather expands itself is taken in natural order, comparing runs of
digits as numbers, so `s2` comes before `s10`; a glob the shell expands is in
the shell's order, which is usually `s1, s10, s2`. detk's other tools match
samples by name, so the order rarely matters.

**Features.** The rows follow the first sample's features. Samples quantified
against the same index or annotation list the same features, so by default a
difference is an error that says which samples lack how many features, with
examples; it usually means a sample was quantified against another annotation.
When the difference is expected, `--on-mismatch=fill` keeps every feature
(features some samples lack are appended in order of appearance) and writes
`0` where a sample lacks one, and `--on-mismatch=drop` keeps only the features
every sample lists.

The report records the format, the column, the samples and their source
files, the number of features, how many features and values were filled or
dropped with examples, and htseq-count's summary lines. The input files are
listed in the module's parameters (`files`).

[salmon]: https://combine-lab.github.io/salmon/
[kallisto]: https://pachterlab.github.io/kallisto/
[htseq-count]: https://htseq.readthedocs.io
[featureCounts]: https://subread.sourceforge.net/featureCounts.html

## `tidy`

Subset both the counts columns and the column data rows by intersection,
returning new outputs for both. The tidied column data is only written if you
pass `-p`.

```text
Usage:
    detk-util tidy [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
    -p FILE --column-data-output=FILE  Destination of tidied column data
```

## `tidy-counts`

Subset and order the counts file columns according to the rows of the column
data file. Fails if the column data contains samples missing from the counts
file.

```text
Usage:
    detk-util tidy-counts [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
```

## `tidy-covs`

Subset and order the column data rows according to the columns of the counts
file. Fails if the counts file contains samples missing from the column data.

```text
Usage:
    detk-util tidy-covs [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied column data [default: stdout]
```

## `annotate`

Add feature metadata, such as gene symbols, to a result table (for example
the output of `detk-de`) by joining it with a mapping table on the feature
IDs. The mapping is a plain delimited file you supply, so the result does not
depend on a network service or on when it was run: a BioMart export, a table
derived from a GTF, or a dump of a Bioconductor `org.*.db` package all work.

```text
Usage:
    detk-util annotate [options] <result_fn> <mapping_fn>

Options:
    -i FIELD --idcol=FIELD  Column in the result file holding the feature IDs to
                            join on [default: 0]
    --map-from=COL          Column in the mapping file matching the result IDs
                            [default: 0]
    --map-to=COLS           Comma-separated mapping columns to add, or 'all' for
                            every column but --map-from [default: all]
    --strip-versions        Strip trailing .N version suffixes from Ensembl-style
                            IDs on both sides before joining
    --drop-unmapped         Drop result rows with no mapping instead of leaving
                            their added columns empty
    -o FILE --output=FILE   Destination of the annotated table [default: stdout]
```

Columns are named by header or by 0-based position. The result table is read
and written back as text, so it keeps its rows, their order, its columns and
their order, and every value as written, including numeric IDs such as Entrez
IDs with leading zeros (`007` stays `007` and matches `007` in the mapping).
The added columns come after the result's own; with `-i` naming a column other
than the first, that column stays where it was.

- An ID is **mapped** when at least one mapping row gives it a non-empty value
  in one of the added columns. A mapping row whose added columns are all empty
  is ignored, so with `--map-to=hgnc_symbol` an ID whose only rows have no
  symbol is unmapped, even though the mapping lists it.
- An unmapped ID gets empty added columns, unless `--drop-unmapped` removes
  the row.
- An empty or missing ID (an empty cell, `NA`, `NaN` and the other strings
  pandas reads as missing) is never joined: it counts as unmapped, and the
  report counts these rows separately.
- An ID with several mapping rows (one Ensembl gene with two Entrez IDs, say)
  gets the distinct values of each added column joined with `;`.
- An added column whose name the result table already has is renamed with the
  suffix `_annot`.

Version suffixes are the most common reason a join silently finds nothing:
`ENSG00000141510.17` in the counts does not match `ENSG00000141510` in a
BioMart export. `--strip-versions` removes them before joining, and the log
warns with example IDs when some features stay unmapped.

```bash
detk-util annotate --strip-versions --map-to=hgnc_symbol \
    -o de_results_annotated.csv de_results.csv biomart_export.tsv
```

The report records how many result rows were mapped, left unmapped, had an
empty or missing ID, matched several mapping rows or were dropped (these count
rows, so a duplicated ID counts once per row), the columns added and up to ten
distinct unmapped IDs.
