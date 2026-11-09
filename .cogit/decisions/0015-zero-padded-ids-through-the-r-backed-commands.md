---
template: adr
state: Proposed
authority: [human]
date: 2026-11-09
from: {node: release/padded-ids, step: s1}
applies: [release/padded-ids]
revisions:
  - {date: 2026-11-09, by: DETK/developer, change: "Narrow to all-numeric ID columns; add enrich fgsea, util tidy-counts/tidy-covs and all-numeric versioned IDs", why: review of s2}
  - {date: 2026-11-09, by: DETK/developer, change: only detk-de deseq2 stops on zero-padded sample names, why: second review of s2}
  - {date: 2026-11-09, by: DETK/developer, change: "the deseq2 check is de.py's own; vst reads no sample information", why: third review of s2}
---

# Zero-padded IDs through the R-backed commands

## Background

Feature IDs such as `007` used to be read by pandas as the number 7.
release/padded-ids (#48) fixes the shared counts reader: `007` now stays
`007`, matches a lengths or mapping file, and every command that reads
counts through that reader in Python writes it back as `007`. Four
commands hand the counts to R through wrapr: `detk-de deseq2`, `detk-de
firth`, `detk-transform vst` and `detk-transform rlog`. For them the IDs
still come back as `7` when the whole ID column looks numeric. Three
Python commands that read their tables with a plain `read_csv` instead
of the shared reader have the same gap: `detk-enrich fgsea`,
`detk-util tidy-counts` and `detk-util tidy-covs`.

## Context

What changes at the R boundary with #48: wrapr writes the counts with
`DataFrame.to_csv`, so the CSV R reads now holds `007` where it held `7`.
The R scripts then re-type it. deseq2 and firth read the counts with
`read.csv(header=T, as.is=T)` and take the first column as row names;
vst and rlog use `read.csv(row.names=1)`. In both, `read.table` runs
`type.convert` on the ID column before it becomes row names, so `007`
becomes the row name `"7"`. (`as.is` only stops factors.) Like pandas,
`type.convert` does this only when every ID in the column looks numeric:
a mixed column (Ensembl IDs plus `007`) stays text, so `007` survives R
and wrapr's read-back. An all-numeric versioned column is worse than
re-typed: `1.10` and `1.1` both become 1.1, so R stops on duplicate row
names. The result is
written back as `7` and wrapr reads it with `pd.read_csv(index_col=0)`,
which would re-type it as an integer even if R had kept the text. The
output is therefore unchanged from before #48: `7`, not a regression.

Sample names behave the same way: a sample-info file with `001` now
matches a counts header `001` in Python (before #48 it failed there), but
the R script of `detk-de deseq2` reads the metadata with
`read.csv(row.names=1)`, and its own check in `de.py`,
`stopifnot(colnames(cnts) == rownames(design.mat))`, would compare `001`
with `1` and stop. `firth` has no such check, `vst` reads no sample
information, and `rlog` reads it without comparing names. Plain numeric sample names (`1`, `2`) now work end to
end, where before #48 they failed in Python.

The same gap outside R (found in the review of #56, step s2):
`detk-enrich fgsea` (`de_toolkit/enrich.py`, the result file) reads with
a plain `pandas.read_csv`, so an all-numeric result ID column turns `007`
into `7` before fgsea sees it, and it no longer matches `007` in the GMT
file. `detk-util tidy-counts` and `tidy-covs` (`de_toolkit/util.py`)
re-read the counts and the covariates with `read_csv(index_col=0)` and
compare the covariate index with the counts columns, so sample names
`001..004` compare as integers against text and both commands exit 1
(they failed on main too). `detk-util annotate` already reads as text.

R is not installed on the machine that made #48, so none of this could be
run; it is read from the scripts and from `read.table`'s behaviour. The
fix lives in `de_toolkit/de.py`, `de_toolkit/transform.py` and
`de_toolkit/wrapr.py` (and, for the Python gap, `de_toolkit/enrich.py`
and `de_toolkit/util.py`), outside the node's scope (`common.py`,
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

Option 2, chosen by Adam on 2026-11-09: this node keeps to the commands
that read counts in Python, and a follow-up node before 1.0
(`release/r-ids`) carries `007` through the R-backed commands, `detk-enrich
fgsea` and `detk-util tidy-counts`/`tidy-covs`, with an R-gated test.

## Consequences

Until it is settled, `detk-de deseq2`/`firth` and `detk-transform
vst`/`rlog` write an all-numeric column of zero-padded IDs as `7` (as
before), all-numeric versioned IDs stop on duplicate row names, and
zero-padded sample names stop `detk-de deseq2` at its sample check
(`stopifnot` in `de.py`); `firth` has no such check, `vst` reads no sample information
(`transform.py` builds its colData from column positions), and `rlog`
reads it without comparing names (read from the source, not run); the CHANGELOG
entry for #48 says so for the R-backed commands. `detk-enrich fgsea`
loses `007` in an all-numeric result column and `detk-util
tidy-counts`/`tidy-covs` stop on zero-padded sample names, as before #48.
Choosing option 1 or 2 means a change to three modules and an R-gated
test (five modules if the enrich and tidy readers go with it, each a
switch to the shared reader or to text IDs); option 3 means a sentence
in the docs of those commands.
