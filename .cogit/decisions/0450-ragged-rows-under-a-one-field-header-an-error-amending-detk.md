---
template: adr
state: Accepted
authority: [human]
date: 2026-11-23
from: {node: release/ragged-sheet, step: s2}
applies: [release/ragged-sheet]
issue: 152
revisions:
  - {date: 2026-11-23, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A, under Adam's delegation via the driver session, 2026-11-20 (DETK-0063): the change is Adam's own request (2026-11-22), implemented and reviewed in PR #149; this record writes it down where the next reader of DETK-0320 will find it"}
---

# Ragged rows under a one-field header: an error, amending DETK-0320's agreement rule

## Background

detk guesses a table's delimiter. When the header has none of
`SNIFF_DELIMITERS`, it guesses from the data lines instead, so that R's
one-column sample sheet (`"condition"` over `"S1","a"`) reads as two
columns (#136). DETK-0320 (Accepted, Option B) set two conditions on a
delimiter found that way: (i) space counts only when the line's first
field is quoted, and (ii) the first data lines must all split on it into
the same number of fields, "otherwise the table is one column".

release/ragged-sheet (#145, PR #149), at Adam's request on 2026-11-22,
changes what happens when (ii) fails: a one-field header over data lines
that split unalike on a delimiter that counts under (i) (`condition` over
`S1,a`, `S2`, `S3`) is now an error, exit 1, naming the file, the
delimiter and the first two lines whose field counts differ. Condition
(i) is unchanged, so every space case DETK-0320 keeps one column
(unquoted IDs with spaces) still reads as one column.

## Context

DETK-0320's text still says, under Option B and Consequences, that
"rows that do not agree … mean one column", and that the agreement check
"stops a single odd first row from setting the delimiter for the whole
file". After #149 a single odd row stops the read instead. The node's
plan notes judged that no decision record was needed (the change is
within DETK-0063 and leaves the space cases alone), but the node's own
objective says it "amends DETK-0320's 'else one column'", and an
Accepted record that describes a rule the code no longer follows will
mislead the next reader of `_sniff`.

The node's acceptance also said "every existing case in
tests/common/test_read_delimited.py … passes unchanged", which
contradicts its objective for the one existing test that asserted the
old reading (`test_data_lines_that_split_unalike_mean_one_column`, the
objective's own example). The developer replaced it with error tests
covering both of its inputs.

Criteria: (1) the record matches the code; (2) the human stays the
author of changes to an Accepted decision; (3) little ceremony for a
change Adam already asked for.

## Options

**A. Accept this record as the amendment, and add a revision line to
DETK-0320 pointing here.** DETK-0320 keeps its Option B for (i); its
"otherwise one column" for (ii) is replaced, for delimiters that count,
by the error. Meets (1) and (2); one `cogit decision accept` and one
`cogit decision revise`.

**B. Revise DETK-0320 in place only** (`cogit decision revise DETK-0320
-m ...`) and reject this record as redundant. Meets (1) and (2), slightly
less ceremony, but the revision line is the only trace of why the rule
changed.

**C. Record nothing.** The CHANGELOG and the node say it. Fails (1):
DETK-0320 stays Accepted with text the code contradicts.

## Decision

Recommended (reviewer, not accepted): **A**. The change is Adam's own
request and is already implemented and reviewed in PR #149; this record
only writes it down where the next reader of DETK-0320 will find it, and
records that the acceptance's "existing cases pass unchanged" did not
apply to the one test that asserted the removed behaviour.

## Consequences

- On acceptance: `cogit decision revise DETK-0320 -m "Option B (ii)
  narrowed by DETK-0450: data lines that split unalike on a delimiter
  that counts under (i) are an error, not one column"`.
- Lines that split on no delimiter that counts (a bare ID list, quoted
  IDs holding a comma, unquoted IDs with spaces) are one column as
  before, with no warning.
- Known limit: the line numbers in the error count non-blank lines, so a
  blank line within the first 11 lines after `skiprows` makes them off
  by one or more; the quoted line text still identifies the lines.
- Revisit if a real sample sheet that should read as one column is
  rejected by the error.
