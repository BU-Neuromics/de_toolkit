---
template: adr
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release/cli-messages, step: s1}
applies: [release/cli-messages]
issue: 126
revisions:
  - {date: 2026-11-21, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's choice, relayed via the driver session, 2026-11-20: Option B, and binds tighter than or, both left-associative; folded into release/cli-messages (PR #127)"}
---

# How and / or group in detk-filter expressions for 1.0

## Background

`detk-filter` keeps the rows of a counts matrix that pass a filter
expression written in a small language: clauses such as `mean(all) > 5`
joined with `and` and `or`, grouped with parentheses. Without
parentheses, an expression that mixes the two, `A and B or C`, needs a
rule for which joins first. Once 1.0 is tagged the CLI, and so what a
filter expression keeps, is part of the promise (DETK-0001): changing the
rule afterwards would silently change the rows an existing command keeps.

## Context

The grammar in `de_toolkit/filter.py` declares no precedence. ply reports
it as 4 shift/reduce conflicts (each of `and`/`or` after `expression
and|or expression`) and resolves every one as a shift. So today `and` and
`or` have **equal precedence and group to the right**:

- `A and B or C` is `A and (B or C)`
- `A or B and C` is `A or (B and C)`

Python, SQL, R (`&&`/`||`), awk and Miller all give `and` higher
precedence than `or` and group left to right, so `A and B or C` is `(A and
B) or C` there. A user writing `mean(all) > 5 and nonzero(all) > 0.9 or
mean(all) > 100` (the docs' example, which they write with parentheses)
without parentheses today gets fewer rows than they expect and no warning.
`docs/tools/filter.md` says only that terms combine with and/or and
parentheses group arbitrarily; it does not state the rule.

release/cli-messages (#124) had the choice "resolve by precedence or
pin". It pins: the conflict count is fixed by a test
(`tests/filter/test_filter_parser.py`), and the grouping above is
asserted expression by expression, so nothing a user runs changes in
that PR. Criteria: least surprise for users who know any other language;
no silent change after 1.0; the 0.x behaviour users may rely on; size of
the change.

## Options

**A. Keep today's rule for 1.0 and document it.** Equal precedence,
right grouping, pinned as now; add a sentence and an example to
`docs/tools/filter.md` (and `detk-filter --help`). No result changes.
Freezes an unusual rule into the 1.0 promise; users who don't read the
docs keep getting the surprising grouping.

**B. Conventional precedence before 1.0: `and` binds tighter than `or`,
both left-associative.** A `precedence` table in `filter.py` (`('left',
'OR'), ('left', 'AND')`), which takes the conflict count to 0 (the pin
test then asserts 0). `A and B or C` becomes `(A and B) or C`. Changes
the rows kept by an unparenthesized mixed expression written for 0.x; a
CHANGELOG entry under Changed says so. Parenthesized expressions, and
ones using only `and` or only `or`, keep their result (both are
associative).

**C. Require parentheses when and and or are mixed.** A usage error
(exit 2) naming the expression and asking for parentheses. Never
silently wrong, in either convention; rejects command lines 0.x accepted.

## Decision

Recommended: **B**, as a small follow-up before release/cut (or folded
into release/cli-messages if accepted before its review). 1.0 is the last
point at which the rule can change without breaking the promise, and B
is what every language a detk user knows does; the 0.x behaviour it
changes is undocumented and affects only unparenthesized mixed
expressions. C is the safe alternative if a silent change of 0.x results
is unacceptable. Not chosen by the developer: it changes what existing
commands keep, which is the human's call.

## Consequences

- With B: the pin test asserts 0 conflicts; the grouping tests flip for
  the two mixed expressions; docs/tools/filter.md states the rule;
  CHANGELOG under Changed.
- With A: docs only; the pin stays at 4.
- With C: a check after parsing that a non-parenthesized `and` and `or`
  do not meet; tests for the message.
- Revisit if the filter language grows `not` or other operators.
