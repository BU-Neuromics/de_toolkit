---
kind: task
objective: 'detk commands that take a design or a filter expression print only what the user needs: an invalid design reads ''Invalid design: ...'', detk-filter writes no parser-generator noise, and a design beginning with ''-'' is read as the design'
acceptance:
  - 'an invalid design that formula syntax parsed but could not build (an unknown column, a level missing from the data, a number-like term under DETK-0190) prints ''Invalid design: <reason>'', not ''Invalid design, detk formula syntax could not parse it: ...'' (common.py, the InvalidDesignException raised from the design setter); a design the syntax cannot parse at all may say so; tests assert the message for an unknown column, a missing level and a syntax error, through CountMatrix and through detk-de on the command line'
  - 'a successful detk-filter run writes nothing to stderr: no ''Generating LALR tables'' and no ''WARNING: 4 shift/reduce conflicts'' from ply.yacc (filter.py builds the parser with its logs quiet, or once); the four shift/reduce conflicts are resolved by precedence or pinned: a test fails if the grammar''s conflict count changes, and the existing filter tests show each ambiguous expression parses as documented; a test runs detk-filter and asserts empty stderr'
  - a design argument beginning with '-' (e.g. '-2.5 ~ counts') is read as the design in every command that takes one (detk-de's subcommands, detk-transform vst), not rejected as 'unrecognized arguments', so it reaches DETK-0190's message; options still parse anywhere on the line, and '--' still ends them; cli-pin rows for the '-' design in tests/cli; CHANGELOG under Fixed
from: [DETK-0190]
scope: [+de_toolkit/common.py, +de_toolkit/filter.py, +de_toolkit/de.py, +de_toolkit/transform.py, tests/common/, tests/filter/, tests/formula/, tests/de/, +tests/cli/cli_cases.py, +tests/cli/cli_tables.py, +tests/cli/test_cli_parse.py, +CHANGELOG]
issue: 124
visited: 8628a94
---

# Design and filter commands say only what went wrong

## Implementation plan

- [x] @developer Say 'Invalid design: <reason>' for designs that parsed but could not be built, quiet ply.yacc's table and conflict output in detk-filter (pinning the conflict count), read a design beginning with '-' as the design; tests and cli-pin rows; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: run detk-de with an unknown column, a missing level and '-2.5 ~ counts', and detk-filter on a real expression, and read stderr as a user would <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 from bugs found by node sessions and reviewers:

- The release/parse-errors reviewer (#113): `CountMatrix.design`'s setter
  in `common.py` (about line 670) wraps every `FormulaParseError` as
  "Invalid design, detk formula syntax could not parse it: ...", also when
  the formula parsed and the failure is an unknown column or a level
  missing from the data. The prefix sends users looking for a syntax error.
- Pre-existing: `detk-filter` prints "Generating LALR tables" and
  "WARNING: 4 shift/reduce conflicts" on stderr on every run, because
  `filter.py` builds the ply parser in a temporary directory each time with
  ply's default logging.
- Pre-existing, reproduced on main at 996633c: `detk-de deseq2 '-2.5 ~
  counts' x.csv y.csv` gives "unrecognized arguments: -2.5 ~ counts"
  (argparse takes the leading '-' for an option); with a leading space it
  reaches the formula. Under DETK-0190 such a design is a usage error
  anyway, so the fix is that the user gets DETK-0190's message naming the
  term, not an argparse one. Where the fix lives (a shared parse step in
  `common.py`, or the commands' positionals) is the developer's.

Grouped as one node: each is the message a user sees from a design or a
filter expression, and none needs a decision (within DETK-0063). No open
node branch touches `common.py`, `filter.py`, `de.py` or `transform.py`
(release/miller-recipes edits `formula.py`, which this leaves alone), so it
has no prev and is ready now. Before release/cut.
