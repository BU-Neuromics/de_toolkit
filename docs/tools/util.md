# `util` — counts, column data and result file utilities

Functions for tidying up counts and [column data](../concepts.md) files —
mostly subsetting one or the other so the sample IDs and their order match.
Combined with `csvgrep` from [csvkit], this is useful for extracting subsets
of samples for downstream differential expression analysis. `annotate` adds
feature metadata, such as gene symbols, to a result table.

[csvkit]: https://csvkit.readthedocs.io

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
