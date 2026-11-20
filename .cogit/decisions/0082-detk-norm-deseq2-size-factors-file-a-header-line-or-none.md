---
template: adr
state: Proposed
authority: [human]
date: 2026-11-20
from: {node: release/size-factors, step: s2}
applies: [release/size-factors]
issue: 93
---

# detk-norm deseq2 --size-factors file: a header line or none

## Background

`detk-norm deseq2 --size-factors=FILE` writes the DESeq2 size factors
(DETK-0029, Option A; node release/size-factors, PR #88). The help says
"a two column tab separated file: sample name and size factor". The
developer wrote it with no header line, one row per sample, and named
that a decision within the node. Once 1.0 is tagged the file's layout is
part of the CLI surface (DETK-0001), so whether its first line is a
header cannot change later without breaking readers. The reviewer of
PR #88 raised it as a decision rather than settle it.

## Context

- The help, DETK-0029 and the node's acceptance say "two columns, sample
  name and size factor, one row per sample"; none says whether there is a
  header. A header row leaves the file two columns with one data row per
  sample.
- The usual readers take the first line as a header by default: pandas
  `read_csv(f, sep="\t")` and R `read.delim(f)` / `read.csv`. On a
  headerless file they silently turn the first sample into the column
  names and return one row too few, with no error. Only `read.table`
  (header=FALSE) and `header=None` / `header=FALSE` read it right.
- The file is meant for agents and for reuse in R (DETK-0029). An agent
  that has not read the help cannot tell what the columns are from the
  file itself.
- Every other detk table output (the normalized counts, stats, filter
  output) has a header row; the counts CSV's first header cell names the
  ID column.
- Criteria: no silent misreads by default readers; self-describing for
  agents; consistent with detk's other outputs; least churn (the change is
  one line plus tests and the help sentence).

## Options

### Option A: a header line `sample<TAB>size_factor`

The first line names the columns; then one row per sample. Default
pandas and R readers read it correctly (`read.delim(f, row.names=1)`,
`read_csv(f, sep="\t", index_col=0)`); the file says what it holds;
matches detk's other outputs. Costs one line in `write_size_factors`, the
tests, and a help sentence. A reader passing `header=FALSE` would get
the header as a sample, but no such reader exists yet: the option wrote
nothing before this PR.

### Option B: no header (as PR #88 has it)

One row per sample only. Matches a literal reading of "one row per
sample"; `read.table` and `header=None` read it. Default `read.delim` and
pandas lose the first sample silently; the file does not describe itself.

## Decision

Recommended: Option A, a `sample<TAB>size_factor` header line, stated in
the `--help` text (and so the skill's commands.md) and the CHANGELOG.
It removes a silent misread under the default readers and makes the file
self-describing for agents, at the cost of one line, before 1.0 freezes
the format.

## Consequences

PR #88 adds the header, says so in the help and CHANGELOG, and the tests
read the header. The skill's commands.md copies the new help text.
docs/example.md can show the first lines of the file. Revisit only if a
consumer that requires a headerless file appears before the tag.
