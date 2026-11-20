---
template: adr
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release/cli-migrate, step: s4}
applies: [release/cut]
issue: 85
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A, make each option do what its help says, as DETK-0029 did for --size-factors: the reviewer's recommendation, accepted under Adam's delegation via the driver session, 2026-11-20 (DETK-0063: within the 1.0 scope, the 1.0 promise unchanged). Planned as release/help-options, after release/cli-migrate and release/cli-gaps, before release/cut."}
---

# Options help lists that do nothing: detk-transform --rda, detk-stats summary --color-col, rlog --blind

## Background

- Proposed by: the reviewer session on release/cli-migrate (step s4),
  2026-11-20, from what the developer found and left in s3

The argparse migration (release/cli-migrate) kept every option as it was
under docopt and wrote a one-line description, metavar and default for
each, as DETK-0025 Option B promises. Three options listed in help do not
do what their description says. They did not work under docopt either;
the migration only made their help explicit. Under DETK-0001 the CLI,
help included (DETK-0025), is the 1.0 promise, and DETK-0029 settled the
same question for `detk-norm deseq2 --size-factors` (implement it). These
three are in no node or issue.

1. **`detk-transform vst|rlog --rda FILE`**: help says "Write the R result
   objects of the analysis to FILE with saveRDS()". `transform.py` declares
   it and never reads `args.rda`, so nothing is written, with no warning
   and exit 0. `detk-de` does honour its `--rda` (`de.py` passes
   `rda=args.rda` to the R wrapper).
2. **`detk-stats summary --color-col COL`**: help says "Column of the
   column data to color the output plots by". `stats.py` declares it and
   never reads it. It is in `detk-stats summary`'s help example and in
   `examples/airway/run.sh` (`--color-col=dex`), so an agent copying either
   gets no coloring and no warning.
3. **`detk-transform rlog --blind BOOL`**: help says "Passed to DESeq2
   rlog(blind=); when not given, blind is True", and the metavar
   convention says BOOL is True or False. The value is passed on as the
   string the user typed. In Python, `"False"` is truthy, so
   `RlogCounts` keeps the blind design `~ 1` and does not attach the
   column data. R then reads `blind="False"` as FALSE, so DESeq2 runs a
   non-blind rlog against the placeholder design. A non-blind rlog with
   the user's design cannot be asked for from the command line.

## Context

- DETK-0025: help states facts an agent can rely on. An option whose help
  describes an effect it does not have is a wrong fact.
- DETK-0029 is the precedent: an inert option that the docs or example
  use was implemented rather than removed.
- Each fix is small and touches the same modules as release/cli-gaps
  (`transform.py`, `stats.py`, tests/cli/).
- Criteria: help states only what works; least churn before the tag; no
  documented command line silently changes meaning.

## Options

### Option A: make each do what its help says (recommended)

1. `--rda` in detk-transform vst and rlog saves the R objects as
   detk-de's does (the same wrapr `rda=` argument).
2. `--color-col` colors the summary plots by that column of the column
   data. If the summary has no plot it can color, fall back to B for this
   option.
3. `--blind` parses `True`/`False` (case-insensitive) to a bool at parse
   time, with any other value a usage error (exit 2), so that
   `--blind False` runs the non-blind rlog with the user's design and
   column data.

Each change gets a cli-pin or module test and a CHANGELOG line under
Fixed. The example, the skill and the help stay as they are.

### Option B: remove what does not work

Drop `--rda` from detk-transform, `--color-col` from detk-stats summary
(and from its example and run.sh), and make `--blind` a flag or drop it.
Less code, but it removes documented options (breaking under semver) and
changes the example.

### Option C: leave them for after 1.0

Ship 1.0 with help that lists three options that do nothing or the wrong
thing. Against DETK-0025's facts promise; fixing them later is still a
behaviour change.

## Decision

Option A, accepted 2026-11-20 under Adam's delegation via the driver
session (DETK-0063: within the 1.0 scope, and it keeps the 1.0 promise
rather than changing it), on the reviewer's recommendation and DETK-0029's
precedent: `--rda` in detk-transform vst and rlog saves the R objects as
detk-de's does; `--color-col` colors detk-stats summary's plots (falling
back to Option B for that option only if the summary has no plot it can
color, recorded as a new decision); `--blind` is parsed to a bool, so
`--blind False` runs the non-blind rlog with the user's design. The work is
release/help-options.

## Consequences

Under A or B, a follow-up node under `release` (or a step added to
release/cli-gaps, which already edits these modules after cli-migrate)
does the work before release/cut, which this record applies to. It does not
block release/cli-migrate:
the migration changed none of these behaviours.
