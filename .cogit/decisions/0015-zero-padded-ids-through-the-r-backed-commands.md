---
template: adr
state: Proposed
authority: [human]
date: 2026-11-09
from: {node: release/padded-ids, step: s1}
applies: [release/padded-ids]
---

# Zero-padded IDs through the R-backed commands

## Background

Feature IDs such as `007` used to be read by pandas as the number 7.
release/padded-ids (#48) fixes the shared counts reader: `007` now stays
`007`, matches a lengths or mapping file, and every command that runs in
Python writes it back as `007`. Four commands hand the counts to R through
wrapr: `detk-de deseq2`, `detk-de firth`, `detk-transform vst` and
`detk-transform rlog`. For them the IDs still come back as `7`.

## Context

What changes at the R boundary with #48: wrapr writes the counts with
`DataFrame.to_csv`, so the CSV R reads now holds `007` where it held `7`.
The R scripts then re-type it. deseq2 and firth read the counts with
`read.csv(header=T, as.is=T)` and take the first column as row names;
vst and rlog use `read.csv(row.names=1)`. In both, `read.table` runs
`type.convert` on the ID column before it becomes row names, so `007`
becomes the row name `"7"`. (`as.is` only stops factors.) The result is
written back as `7` and wrapr reads it with `pd.read_csv(index_col=0)`,
which would re-type it as an integer even if R had kept the text. The
output is therefore unchanged from before #48: `7`, not a regression.

Sample names behave the same way: a sample-info file with `001` now
matches a counts header `001` in Python (before #48 it failed there), but
the R scripts read the metadata with `read.csv(row.names=1)` and DESeq2's
`stopifnot(colnames(cnts) == rownames(design.mat))` would compare `001`
with `1` and stop. Plain numeric sample names (`1`, `2`) now work end to
end, where before #48 they failed in Python.

R is not installed on the machine that made #48, so none of this could be
run; it is read from the scripts and from `read.table`'s behaviour. The
fix lives in `de_toolkit/de.py`, `de_toolkit/transform.py` and
`de_toolkit/wrapr.py`, outside the node's scope (`common.py`,
`tests/common/`, `docs/tools/norm.md`, CHANGELOG), and the node's
acceptance says `007` is kept in every tool's output.

## Options

1. **Widen this node** to the R-backed commands: read the ID column (and
   the metadata row names) with `colClasses="character"` for the first
   column in the four R scripts, and have wrapr read its output's first
   column as text. Meets the acceptance in full for 1.0; changes three
   files outside the scope and can be checked only where R and DESeq2 are
   installed (CI's R job, if it runs them).
2. **Follow-up node before 1.0** for the R boundary, with an R-gated test
   that round-trips `007` through each command. Keeps this PR to the
   shared reader; the 1.0 CHANGELOG says the R-backed commands still
   write `7` until it lands.
3. **Leave it after 1.0**, documented as a known limitation of the
   R-backed commands. Least work; leaves `007` unmatched for anyone
   annotating DESeq2 results with a mapping file that keeps the padding.

## Decision

Proposed, for Adam: option 2. The Python side is fixed and tested here;
the R side needs its own test run with R, and widening this node's scope
is Adam's call, not the developer's.

## Consequences

Until it is settled, `detk-de deseq2`/`firth` and `detk-transform
vst`/`rlog` write zero-padded IDs as `7` (as before), and zero-padded
sample names stop at DESeq2's sample check; the CHANGELOG entry for #48
says so. Choosing option 1 or 2 means a change to three modules and an
R-gated test; option 3 means a sentence in the docs of those commands.
