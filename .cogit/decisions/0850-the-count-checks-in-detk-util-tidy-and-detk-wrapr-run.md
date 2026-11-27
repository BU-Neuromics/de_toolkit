---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/count-checks-readers, step: s2}
applies: [release-1-0-1/count-checks-readers]
issue: 206
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A. Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27"}
---

# The count checks in detk-util tidy and detk-wrapr run

## Background

- Proposed by: the @reviewer session of release-1-0-1/count-checks-readers s2, 2026-11-27

release-1-0-1/count-checks-readers (#201, PR #203) makes the commands in
de_toolkit/norm.py, de.py, transform.py, stats.py, filter.py and outlier.py
check a counts file as read (DETK-0830). Two other commands read a counts
matrix and do not run the check: `detk-util tidy`, `tidy-counts` and
`tidy-covs` (de_toolkit/util.py, `_tidy_main`, which calls `read_id_table`
directly) and `detk-wrapr run` (de_toolkit/wrapr.py, `CountMatrixFile(...)`
with no `check`). Both files are outside the node's scope.

## Context

- On the PR head (c9cdf4b), `detk-util tidy-counts` on `gene,A,A,B,C` with
  column data naming A, B and C exits 0 and writes `gene,A,B,C`. It drops
  the second `A` (read as `A.1`) and logs only "counts columns lost: 1".
  This is the silent drop the node's first acceptance criterion describes.
- The node's objective says "every command that reads a counts matrix". Its
  acceptance lists the commands by module, and util and wrapr are not on
  the list. docs/concepts.md and the CHANGELOG entry in the PR say "every
  command".
- Under DETK-0601, a repeated sample header or feature ID exits 1. The
  tidy commands are where a user would go to line up samples, so a silent
  drop there is the worst place for it.
- `detk-wrapr run` passes the counts to a user's own R script. The
  duplicate checks fit it. Whether it needs raw counts depends on the script.

## Options

**A. Follow-up node** (recommended): a new release-1-0-1 task
(count-checks-util). `detk-util tidy*` and `detk-wrapr run` run the
duplicate checks only (`check="ids"`, or `check_counts(..., values=False)`
on the table `_tidy_main` reads). Its scope is de_toolkit/util.py,
de_toolkit/wrapr.py, tests/, docs/concepts.md and CHANGELOG. In #203, the
docs and CHANGELOG list the commands that run the check and stop saying
"every command".
- Keeps #203 to its planned scope. The fix is about four lines per file,
  done after #203 lands.

**B. Widen #203's scope** to util.py and wrapr.py, and add the two commands
there.
- One PR closes the objective as worded. It adds another scope change to a
  node already widened once (DETK-0830) and needs another review round.

**C. Leave util and wrapr unchecked**, and document them as exceptions.
- The tidy commands keep dropping a repeated header without a word, which
  is the behaviour DETK-0601 rules out.

## Decision

Recommended: **A**. A small, separate node closes the gap without widening
#203 a second time. #203 only has to stop claiming "every command".

## Consequences

- #203's docs and CHANGELOG name the commands that check. A sentence notes
  that detk-util tidy and detk-wrapr run get the check in the follow-up
  node, or leaves them out until then.
- A new node in release-1-0-1, after count-checks-readers, with the scope
  above. Its reproduction is the tidy-counts case under Context.
- Revisit if 1.0.1 is to ship before the follow-up lands. Then B is the
  cheaper route.
