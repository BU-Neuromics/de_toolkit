---
template: adr
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release/cli-gaps, step: s2}
applies: [release/cli-gaps]
issue: 99
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's delegation via the driver session, 2026-11-20: Option B, fix it in release/cli-gaps' next round (intermixed leaf parsers for every parser with an optional positional, a 3.11-run test per command); restores DETK-0001's CLI promise on a supported Python, no scope change"}
---

# On Python 3.11 an optional positional after an option is rejected: fix before 1.0, and where

- Proposed by: the release/cli-gaps reviewer session, 2026-11-20 (step s2)

## Background

Several detk commands take an optional positional argument after a
required one: `detk-filter <command> <counts_fn> [<cov_fn>]`,
`detk-stats summary|pca <counts_fn> [<cov_fn>]`, `detk-transform rlog
<counts_fn> [<design>] [<cov_fn>]` and `detk-wrapr run <rscript>
[<counts_in>] [<out>]`. Python 3.11 (a supported version) rejects an
optional positional that comes after an option:

    $ detk-stats summary counts.csv -o out.csv cov.csv      # Python 3.11
    detk-stats summary: error: unrecognized arguments: cov.csv   (exit 2)

Python 3.12 and 3.13 accept the same line (an argparse fix that was not
backported to 3.11, which takes security fixes only). Reproduced by the
reviewer on 3.11.16 for detk-stats summary, detk-stats pca and
detk-filter; options first (`-o out.csv counts.csv cov.csv`) works on all
versions. The behaviour predates release/cli-gaps (it came with the
docopt-to-argparse migration, release/cli-migrate); the cli-gaps
developer met it in tests/report/test_report.py and reordered that test's
arguments, which hides it.

## Context

- DETK-0001 makes the CLI the stable 1.0 surface; the same command line
  must not mean one thing on 3.11 and another on 3.12+.
- 0.9 parsed with docopt, which accepts options anywhere among the
  positionals, so `counts.csv -o out.csv cov.csv` worked in 0.9 and fails
  in 1.0 on 3.11 only: an unlisted breaking change on one Python.
- DetkParser already supports `intermixed=True` (parse_known_intermixed_args
  at the leaf parser); detk-util gather uses it.
- No CI pin puts an option between two positionals, so CI's 3.11 job
  passes.
- release/cli-gaps' objective is --column-data, exit codes and
  completion; this is a parsing behaviour of its own.

## Options

### Option A: a new node before 1.0 makes the leaf parsers intermixed (recommended)

A small release node: every leaf parser with an optional positional (or
every leaf parser, for one rule) parses intermixed, so 3.11 behaves as
3.12+ and 0.9; a cli-pin row puts an option between `<counts_fn>` and
`<cov_fn>` for each such command, run in the 3.11 CI job; tests/report
can go back to the natural order. Kept apart from cli-gaps so that PR
stays reviewable and its exit-code work lands now.

### Option B: fix it in release/cli-gaps (step s3)

Same change, in this node: its scope already holds common.py, filter.py,
stats.py, transform.py and wrapr.py. Fewer nodes, but it widens a node
whose objective does not cover it and holds its PR longer.

### Option C: document it

State in help and the docs that on Python 3.11 options come before an
optional positional. Cheapest; leaves the CLI different per Python
version, against DETK-0001.

## Decision

Recommended: Option A. The 1.0 promise needs one command line to mean
the same on every supported Python, and 0.9 accepted it; the fix is
small and already has the mechanism (intermixed). A separate node keeps
release/cli-gaps to its objective. Option B is acceptable if a second
node is not wanted. Awaiting Adam's / the driver's answer.

## Consequences

A node `release/intermixed` (or similar) before the cut, with a 3.11
cli-pin row per command with an optional positional. Intermixed parsing
must keep what gather's CHANGELOG row promises (an option given twice and
`--` stay usage errors). Revisit if 3.11 support is dropped before 1.0.
