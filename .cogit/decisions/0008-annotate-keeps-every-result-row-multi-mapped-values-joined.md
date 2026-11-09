---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/annotate, step: s1}
applies: [release/annotate]
allowed_by: [reasonable]
reason: A result table must not gain or reorder rows when it is annotated
revisions:
  - {date: 2026-11-09, by: DETK/developer, change: "CLI reads the result as text and keeps its column layout; 'mapped' needs a non-empty added value; missing IDs never join; distinct unmapped examples", why: review of s2}
---

# annotate keeps every result row: multi-mapped values joined with ';', clashing columns suffixed _annot

## Background

`detk-util annotate` (DETK-0007) adds columns from a mapping table to a
result table. Real mapping tables are not one-to-one: a BioMart export
lists an Ensembl gene once per Entrez ID, and some IDs have no row at
all. The mapping columns may also share a name with a result column.

## Context

The output is read by people and by the next tool (`detk-enrich`,
spreadsheets). A table of DE results has one row per tested feature;
downstream counts of significant genes, ranks for fgsea and merges by
ID all assume that. Silent data loss or duplication is the failure to
avoid.

## Options

1. **Keep one row per result row**: join the distinct values of a
   multi-mapped ID with `;`, leave unmapped IDs with empty columns
   (dropped only on `--drop-unmapped`), suffix a clashing added column
   with `_annot`. Rows, order and IDs are unchanged.
2. **Expand**: one output row per mapping row (a plain left join).
   Simple, but duplicates features and inflates counts and ranks.
3. **First match**: keep the first mapping row per ID. One row per
   feature, but silently discards information and depends on file
   order.
4. **Error on clashes or multi-mapping**: strict but makes common
   BioMart exports unusable without preprocessing.

## Decision

Option 1. It keeps the result's shape, loses nothing, and the report
counts multi-mapped and unmapped IDs (`num_multimapped`,
`num_unmapped`, `unmapped_examples`) so the user sees what happened.
The result's own (possibly versioned) IDs are kept as written;
`--strip-versions` affects only the join keys. A clashing column is
renamed rather than overwritten so the result's data is never replaced.

Amended after the review of s2:

- The CLI reads the result table as text and writes it back as read,
  so numeric IDs (Entrez) join as strings, keep leading zeros and are
  never turned into floats. The result's columns keep their order and
  its first column stays the index, whichever column `-i` joins on;
  the added columns come last.
- An ID is mapped when at least one mapping row gives it a non-empty
  value in an added column; a mapping row whose added columns are all
  empty is ignored, so `--drop-unmapped` drops such IDs too.
- An empty or missing result ID (empty cell, `NA`, `NaN` and the other
  strings pandas reads as missing) is never joined; it counts as
  unmapped and the report counts it as `num_missing_ids`.
- `unmapped_examples` lists distinct IDs; the counts stay per row.

## Consequences

- A user who wants one symbol per row from a multi-mapped column must
  split on `;` themselves; a `--first` option could be added later
  without breaking this default.
- `;` is the separator; a value that itself contains `;` would be
  ambiguous (rare for symbols and IDs).
- The `_annot` suffix and the `;` separator become part of the 1.0
  output format (DETK-0001).
