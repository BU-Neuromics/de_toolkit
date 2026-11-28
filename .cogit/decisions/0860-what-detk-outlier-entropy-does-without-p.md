---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/outlier-entropy-p}
applies: [release-1-0-1/outlier-entropy-p]
issue: 204
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A (-p defaults to 0.05, the value every documented run uses): the recommendation, accepted under Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27"}
---

# What detk-outlier entropy does without -p

## Background

`detk-outlier entropy` flags the features (genes) whose entropy across the
samples is below a percentile of all the features' entropies: features whose
counts come mostly from one or a few samples. The percentile is `-p N`, a
fraction between 0 and 1 (DETK-0200). `-p` is listed under "options" in
`--help`, docs/tools/outlier.md and the skill's commands reference, so it
reads as optional, but no default is stated anywhere.

## Context

- On v1.0.0, `detk-outlier entropy counts.csv` without `-p` exits 2 with
  `argument -p/--percentile: invalid float value: None`: the option has no
  default, and `main()` converts `None` with `option_value(args,
  "percentile", float)`. Reproduced by the plan session, 2026-11-27, on a
  v1.0.0 install; with `-p 0.5` the same file runs. Found first by the
  count-checks-readers session, whose tests pass `-p` to work around it.
- No record states an intended default. The docopt CLI before the argparse
  move (d85eda7^) also gave none (`-p P --percentile=P  Float value between
  0 and 1`), so the command has never run without `-p`. Every documented
  run uses `-p 0.05`: the `--help` example ("Flag the features below the 5th
  entropy percentile"), docs/tutorials/airway.md, the skill's airway
  reference, and DETK-0200's own example.
- Constraints: 1.0.1 adds no command or option (DETK-0001's promise, the
  outcome's acceptance); each behaviour change is a bug fix with a CHANGELOG
  note (DETK-0600). Either option below keeps every run that passes `-p`
  exactly as it is.
- Criteria: the command does what its help says; an agent or user who
  leaves `-p` out gets either a sensible result or a clear usage error; the
  fix is small.

## Options

### Option A: `-p` defaults to 0.05

The 5th percentile, which every documented example uses. `--help` reads
"between 0 and 1 (default: 0.05)", the flag column is `entropy_p0_05`, and
the params in the module JSON record 0.05 as for an explicit `-p 0.05`.
Matches how the help lists `-p` (under options, beside `-o` and
`--plot-output`, which are optional), and makes the command runnable as its
usage line `detk-outlier entropy [options] <counts_fn>` promises. Cost:
detk chooses a threshold for the user; 0.05 is a convention, not a
statistic of the data.

### Option B: `-p` is required

argparse `required=True`: without `-p` the usage error is argparse's own
("the following arguments are required: -p/--percentile"), exit 2 as now,
and the usage line shows `-p N` outside `[options]`. Nothing new is chosen
for the user and v1.0.0's behaviour (it never ran without `-p`) becomes an
honest message. Cost: the help and docs move `-p` out of the options list,
and a run that leaves it out still fails.

## Decision

**Option A**, `-p` defaults to 0.05: accepted on the recommendation under
Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended
to the post-1.0 plan 2026-11-27. The help, the docs and
the usage line already present `-p` as optional, and every documented run
uses 0.05, so the default writes down what the documentation already
implies rather than changing what the command means; Option B keeps a
failure the docs do not lead anyone to expect. Proposed by the plan
session, 2026-11-27.

## Consequences

- Under A: `de_toolkit/outlier.py` gives `-p` `default="0.05"` and the help
  says so; docs/tools/outlier.md and skills/detk/references/commands.md are
  regenerated from `--help`; tests/cli's table of options records the
  default (`test_option_without_documented_default_is_unset` is about `-o`
  and unchanged); CHANGELOG 1.0.1 under Fixed: "`detk-outlier entropy`
  without `-p` uses the 5th percentile (0.05) instead of failing".
- Under B: the same files, with `required=True` and the usage line; CHANGELOG
  says `-p` is required.
- Revisit if a data-driven default (from the entropy distribution) is wanted:
  that is a new behaviour for release-1-1, not 1.0.1.
