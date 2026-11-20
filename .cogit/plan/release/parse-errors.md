---
kind: task
objective: 'Design formulas and detk-filter expressions never drop a term or select nothing silently: number-like column names follow DETK-0190, a filter group value not in its column is a usage error, and design errors read as plain messages'
acceptance:
  - 'number-like terms follow DETK-0190 as answered (recommended Option A: a term that looks like a number, other than 0 and 1, is a usage error, exit 2, naming it, and saying to rename the column when the column data has one by that name); tests cover 3, 2.5 and -2.5 on each side of ~, with and without a column of that name, so counts ~ -2.5 and -2.5 ~ c no longer lose a term silently; ~ 0 + x and ~ 1 keep their intercept meaning; docs/formulas.md states the rule'
  - detk-filter with a group value not present in its column (e.g. cond[Z]) is a usage error (exit 2) naming the column, the value and the values present, and writes no output file; a group value matching a column of numbers or booleans as written (cond[1] on a 0/1 column) selects those samples; the duplicated warning goes; tests in tests/filter/ and a cli-pin row
  - an invalid design (an unknown column, a misspelled term, a numeric literal formulaic rejects) gives a clean one- or two-line message naming the offending term, with no Python tuple text, no traceback and no ANSI escape codes from formulaic; tests assert the message text for each formula.py error path that wraps a formulaic error; CHANGELOG under Fixed (and the DETK-0190 change under Changed)
from: [DETK-0190]
scope: [+de_toolkit/formula.py, +de_toolkit/filter.py, tests/formula/, tests/filter/, +tests/cli/cli_cases.py, +tests/cli/cli_tables.py, +docs/formulas.md, +CHANGELOG]
prev: [DETK-0190, release/r-design-names, release/help-options]
issue: 112
visited: 09ef1fd
status: done
done: 28dcc55
---

# Formula and filter errors are clear and never silent

## Implementation plan

- [x] @developer Apply DETK-0190 to number-like terms in the formula module, make a filter group value not in its column a usage error (and match numeric and boolean values as written), turn every wrapped formulaic error into a clean message; tests and cli-pin rows; docs/formulas.md; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: try 3, 2.5 and -2.5 on each side of ~, cond[Z] and a misspelled term on the command line, and read each message as a user would <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 from bugs found by node sessions and reviewers.
Reproduced on main at f3a014f:

- `counts ~ -2.5` gives the right side `Intercept` only and `-2.5 ~ c` an
  empty left side, both silently; `counts ~ 2.5` uses the column, and
  `counts ~ 3` is formulaic's "Numeric literals other than `1`" error.
  DETK-0190 (Proposed, recommending Option A) decides the rule; this node
  waits on it.
- `detk-filter 'mean(cond[Z]) > 1'` with no `Z` in `cond`: `ColSpec`
  warns twice (the warning is duplicated in `filter.py`), the clause gets
  an empty frame, and the command exits 0 with a header-only file. The
  group is compared to the column's values as the string written, so
  `cond[1]` on a 0/1 column selects nothing today as well.
- `DesignMatrix` wraps formulaic's errors as
  `f"Misspecified column in design, check term names. {e.args}"`, which
  prints the args tuple, with formulaic's ANSI-coloured caret markup.

After release/r-design-names (in `formula.py`) and release/help-options
(`tests/cli/`), both merging now. Shares `docs/formulas.md` with
release/miller-recipes, which only links its recipes page from it; this
node adds a sentence on column names, so whichever lands second merges
main. Before release/cut.
