---
template: adr
state: Accepted
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/gather, step: s1}
applies: [release/gather]
allowed_by: [reasonable]
reason: "Files get renamed but headers do not; extraction is faithful text; names come from the paths users already organize by sample"
revisions:
  - {date: 2026-11-09, by: DETK/developer, change: htseq files with several count columns are refused unless --column is given; values must be plain finite decimal numbers; the default-naming rationale now says the directory fallback is all or nothing per run; quoted globs expand in natural order, why: review of s2}
  - {date: 2026-11-09, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-09: accept with release/gather"}
---

# gather detects formats by header, extracts one column as written, names samples from paths

## Background

`detk-util gather` (#25) builds the counts matrix every detk workflow
starts from, out of per-sample outputs of salmon (`quant.sf`), kallisto
(`abundance.tsv`), htseq-count and featureCounts. Three choices fix its
behaviour for users and for anything that reads its output: how it tells
the formats apart, what it extracts and writes, and what it calls each
sample's column. All three become part of the 1.0 CLI surface
(DETK-0001).

## Context

Criteria: the matrix must be a faithful copy of what the quantifier
wrote (the issue: "just faithful column extraction"); auto-detection
must not guess wrong silently; the result must read back with detk's
usual `index_col=0` sniffing; sample names must come out right for the
common layouts (one salmon or kallisto directory per sample, where every
file has the same name; one htseq file per sample; one featureCounts
file for many BAMs) without a flag, and be controllable with one flag
when not; and IDs must be kept as written, as `detk-util annotate`
does (DETK-0008).

## Options

Format detection:

1. **By content**: salmon and kallisto by their exact header line,
   featureCounts by its `# Program:featureCounts` line or its
   `Geneid Chr Start End Strand Length` header, htseq-count by a
   header-less first line whose fields after the ID are integers; one
   format for all files, otherwise an error. Robust to renamed files;
   cannot be fooled by a name.
2. **By file name** (`quant.sf`, `abundance.tsv`, `*.counts`). Simple,
   but files are routinely renamed by pipelines, and htseq and
   featureCounts have no fixed names.

Values:

1. **Read as text and write as written** (`9.512` stays `9.512`, `007`
   stays `007`), checking only that each value is a plain finite decimal
   number (optional sign, digits, optional fraction and exponent), as
   quantifiers write them. Faithful;
   consistent with annotate.
2. **Parse as numbers**: a numeric frame for the Python API, but floats
   are rewritten (`42.000` becomes `42.0`) and numeric IDs lose leading
   zeros.

Sample names:

1. **From the path**: the file name without its last extension, or,
   when those are not unique (`quant.sf` everywhere), the parent
   directory's name; `--name-from=REGEX` takes the first group (or the
   whole match) of a regular expression searched in the path. A
   featureCounts count column is named the same way from its header,
   the BAM path featureCounts writes there.
2. **csvgather-style substitutions** (`s:pat:repl:`, several in turn).
   Powerful but harder to read and to quote in Snakemake; the issue
   asks for "regex/substitution", and a capture group covers the
   documented cases.
3. **Strip the common prefix and suffix of all paths.** Clever, but a
   name then depends, character by character, on which other files are
   in the run, and is hard to predict.

## Decision

Content-based detection (option 1), values kept as text (option 1) and
names from the path with `--name-from` as a regex whose first group is
the name (option 1). Detection by content cannot be defeated by a
rename; text keeps the matrix faithful and matches annotate. The
default naming gives the directory name for salmon and kallisto and the
file stem for htseq, which is how those layouts name samples. It is not
independent of the other files: the fallback to directory names is all
or nothing per run, taken when the file stems are not unique among the
files given, so a lone `s1/quant.sf` is named `quant` but `s1` beside
`s2/quant.sf`, and two `counts.txt` in different directories switch
every sample of that run to its directory name. Unlike option 3, the
rule is one coarse switch that is easy to state and predict, and
`--name-from` gives names that never depend on the run. Duplicate sample
names, a non-matching `--name-from`, a value that is not a plain finite
decimal number (so `NA`, `nan`, `inf`, padded values and `1_000` are
refused) and a feature listed twice in one file are errors. The output's index (first)
column is unnamed, as pandas writes an unnamed index, whatever the
source's ID column was called (`Name`, `target_id`, `Geneid`).

Default column: salmon `NumReads`, kallisto `est_counts`, htseq the
count column, featureCounts every count column (one sample per BAM);
`--column` picks another by name or 0-based position. An htseq-count
file with more than one count column (htseq-count 0.13+ run on several
BAMs) has no default: it is refused unless `--column` is given, because
htseq-count writes no header to name the columns and taking the first
would drop the other samples silently. One sample per column with a
positional naming rule was considered and not taken: the names would be
invented rather than read from the file, and the per-sample layout
(one htseq-count run per sample) is the common one. htseq-count's
`__` summary lines are left out of the matrix and recorded in the
report (`htseq_counters`). No transcript-to-gene aggregation.

## Consequences

- A multi-BAM htseq-count file is gathered one column per run
  (`--column=N`); gathering all its columns at once would need a naming
  rule and is left for a later version.
- Glob patterns gather expands itself are taken in natural order
  (`s2` before `s10`); shell-expanded globs keep the shell's order.
- htseq-count 2.x output written with `--with-header` is not detected;
  `--format=htseq` then reads the header as a feature and fails on the
  non-numeric value. A later version could skip such a header.
- The Python API (`Gather`, `gather`) returns text values; callers
  wanting numbers convert with `astype(float)`.
- The module JSON has one `in_file_path`; the inputs are listed in
  `params["files"]` and so appear in the RO-Crate as a parameter, not as
  input File entities. Making them inputs needs a change to
  `de_toolkit/crate.py` beyond the `SUBTOOLS` entry added here (as for
  annotate's mapping file, DETK-0007).
- A tx2gene aggregation flag (issue #25's follow-up) can be added
  without changing these defaults.
