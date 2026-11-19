---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/size-factors]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: implement it"}
---

# detk-norm deseq2 --size-factors: implement or remove

- Proposed by: the planning session, 2026-11-19, under DETK-0025's "address
  all the CLI gaps"

## Background

`detk-norm deseq2` declares `--size-factors=FILE` ("Write out the size
factors found by the DESeq2 method to two column tab separated file").
`norm.py` never reads it, so no file is written, there is no warning,
and the exit code is 0. This is issue #44 and the node
`features/size-factors`, from the review of #42. The worked example uses
it (`examples/airway/run.sh` line 35, `docs/example.md` line 56), and
the skill's `references/commands.md` copies the usage line.

## Context

- The size factors are already computed and kept on the module object
  (`norm.py` line 243, `self.size_factors`). Writing them is a few lines
  plus a test.
- Size factors are useful for explaining a normalization, and for
  reusing it in R.
- Criteria: help states only what works (DETK-0025); least churn before
  the tag.

## Options

### Option A: implement it

Write the two-column tab-separated file the help describes. The example
and the skill stay as they are.

### Option B: remove it

Drop the option, and the example's use of it. Smaller, but it removes a
documented output.

## Decision

Option A, chosen by Adam on 2026-11-19 (relayed by the driver session):
"implement it". `--size-factors=FILE` writes the two-column tab-separated
file the help describes; the example and the skill stay as they are.

## Consequences

The node `features/size-factors` moves to `release/size-factors`, ahead
of `release/cut`, and carries out the choice after `release/cli-migrate`
(both edit `norm.py`).

## Replies

- 2026-11-19, adamlabadorf: Planning note: release/size-factors implements it; with DETK-0029 answered, it waits only on release/cli-migrate.
