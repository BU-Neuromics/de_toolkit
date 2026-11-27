---
template: adr
state: Proposed
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1}
applies: [release-1-0-1/sample-match, release-1-0-1/fgsea-statcol, release-1-0-1/skill-guidance]
issue: 171
---

# Sample sets that differ and an ambiguous fgsea ranking are errors in 1.0.1

- Decided by: Adam, via the driver session, 2026-11-27 (his own decision,
  not delegated); recorded by the plan session

## Background

An external AI-readiness audit of 1.0.0 (Codex, November 2026) found two
ways detk returns a credible result, exit 0, for an analysis that is not the
one asked for. Both reproduced on main (75aacb3):

1. **Sample sets that differ.** `detk-de deseq2` (and every command that
   matches a counts file to a sample information file, through
   `CountMatrix` in de_toolkit/common.py) fits the samples the two files
   share and drops the rest, with nothing above INFO on stderr. With
   samples 001-008 in the counts and 008 renamed 999 in the sample sheet,
   it fitted 7 samples and exited 0. Only `--strict` refuses, and it also
   refuses a mere reordering.
2. **An ambiguous fgsea ranking.** Without `-c`, `detk-enrich fgsea` ranks
   by the last numeric column, which in DESeq2 output is the last term's
   `__padj`: the planted gene set came out NES -2.76, padj 0.5, where the
   signed Wald statistic gives +2.13, padj 0.0003. The skill tells agents
   to always pass `-c`, but the command accepts the omission.

## Context

- The 1.0 promise (DETK-0001, docs/index.md "Stability"): subcommand
  names, arguments, output formats, the module JSON schema and the
  provenance crate follow semantic versioning; DETK-0025 adds what help
  states (each option's default among it) and DETK-0031 the exit codes
  (0 success, 2 usage error, 1 any other failure).
- detk's purpose, in Adam's words for DETK-0001, is to make agent-written
  analyses more reliable and explainable. An agent reads the exit status;
  exit 0 on a silently changed analysis defeats that.
- How each behaviour stands against the promise:
  - fgsea: help documents the default ("the last numeric column if not
    given"), so it is a promised fact. Requiring `-c` where more than one
    column could rank changes that fact, and a command line that ran in
    1.0.0 exits 2 in 1.0.1. On a strict reading that is a breaking change.
  - Sample matching: nothing promises the intersection. docs/concepts.md
    says detk "matches samples up by name" and `--strict` requires the
    same order; the subset is an undocumented side effect, and the error
    text ("at least 2 values in common") is the only hint of it. Making a
    difference an error changes no documented fact; it is a bug fix.
- Semantic versioning defines a patch as backwards-compatible bug fixes,
  where a bug is incorrect behaviour. Who is broken: only command lines
  whose results were the wrong analysis (a dropped sample, a padj
  ranking) or depended on an implicit subset. A run that passes `-c`, or
  whose files hold the same samples (in any order), is unchanged.

## Options

**A. Errors in 1.0.1, as bug fixes** (chosen). Sample sets that differ are
an error naming the samples in only one file (exit 1, a bad input under
DETK-0031); a pure reorder is allowed. fgsea without `-c` is a usage error
(exit 2, DETK-0031) when the table has more than one numeric column besides
the ID column; with one, it ranks by it as before. Each is named under a
"Behaviour changes" heading of the 1.0.1 CHANGELOG with the fix
(`detk-util tidy`, or `-c COL`).

**B. Opt-in strictness in 1.x** (the audit's alternative). Add a flag or
setting that turns these into errors; the default stays. Keeps the
promise to the letter, but the default still gives the silent wrong
answer, which is the finding.

**C. Warnings in 1.0.1, errors in 2.0.** A stderr warning now. Agents and
pipelines read the exit status, not stderr, so the analysis still goes
through.

## Decision

Option A, Adam's decision via the driver session, 2026-11-27: the two
silent-wrong-answer findings are bugs, fixed in 1.0.1 by erroring.
DESeq2, and any command matching counts to sample information, errors
when the sample sets differ (a pure reorder stays allowed); fgsea requires
`-c/--statcol` whenever more than one numeric column could be the ranking.
Both get CHANGELOG notes.

How it squares with the 1.0 promise: the sample-set error changes no
promised fact, so it is an ordinary bug fix. The fgsea change alters a
documented default and is therefore a deliberate, recorded exception
under semver's bug-fix rule: the documented default was itself the
defect, since it ranks by an adjusted p-value with no sign and no stated
choice. It changes only command lines whose results were not the analysis
asked for, fails loudly with the fix named rather than changing any
result silently, and leaves every `-c` command line (the form the skill,
the docs and the examples use) unchanged. The help line for `-c` is
updated in the same release. The exit codes follow DETK-0031 as they
stand: 1 for the sample mismatch (input data), 2 for the missing `-c`
(the command line). This sets no precedent for other documented
behaviour: a change to a promised fact in a patch needs this kind of
record and Adam's decision.

## Consequences

- `release-1-0-1/sample-match` and `release-1-0-1/fgsea-statcol`
  implement it, each with a test that reproduces the audit's case first;
  `release-1-0-1/skill-guidance` updates the skill.
- Tutorials or examples that relied on an implicit subset are fixed with
  `detk-util tidy` in the same node.
- The fgsea module JSON records the ranking it used (statcol, idcol,
  ascending) as params, an open object, so the schema is unchanged.
- Revisit if a user shows a correct analysis that 1.0.1 now refuses with
  no reasonable fix.
