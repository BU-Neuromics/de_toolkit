---
kind: task
objective: 'Design formulas accept the fixed set of transforms DETK-0028 and DETK-0047 define, computed by detk itself and recorded in provenance, with no expression from a formula evaluated by formulaic or R'
acceptance:
  - 'the formula module accepts exactly the transforms DETK-0047 names, in the forms it allows (arguments, nesting, sides, column types), and refuses every other parenthesised term with a FormulaParseError that lists the allowed forms'
  - 'detk computes each transformed column itself in pandas and adds it to the model data under the name DETK-0047 sets; the formula handed to formulaic contains only column names, and a test shows that a term formulaic or patsy would evaluate (e.g. len(x), __import__(...)) is refused before formulaic sees it'
  - 'every name in the resolved design passed to R''s formula() is one R reads as a name (backtick-quoted where it is not syntactic), with a test that a column data column named like a call is never run by the R-backed commands'
  - 'values a transform cannot take, missing values, name clashes and a column literally named like a transform behave as DETK-0047 decides, each with a test and a message naming the column, the transform and the samples'
  - 'the module JSON and the Process Run Crate record the formula as written and each transform as DETK-0047 decides; the module schema stays valid; the crate conformance tests pass'
  - 'detk-de deseq2 and firth give the same results with log2(x) in the design as with a precomputed log2 column in the column data file, shown by the R-gated tests in CI'
  - 'docs/formulas.md has one table of the transforms and their rules in place of the old "patsy" term type; the skill''s formula section mentions them; the formula-pin test for the documented transform is changed on purpose, not deleted; CHANGELOG'
from: [DETK-0028, DETK-0047]
scope: [de_toolkit/formula.py, tests/formula/, docs/formulas.md, +de_toolkit/common.py, +de_toolkit/de.py, +de_toolkit/norm.py, +de_toolkit/transform.py, +de_toolkit/crate.py, tests/de/, tests/report/, +skills/detk/SKILL.md, +CHANGELOG]
prev: [DETK-0028, DETK-0047, release/formula-rename, release/cli-migrate]
---

# Transforms in design formulas

## Implementation plan

- [ ] @developer Implement the DETK-0047 transform set in `formula.py` (parse, check, compute in pandas, name), quote R design names, record `formula` and the transforms in the module JSON and the crate, with tests (including the code-execution refusals and the R-gated equivalence test); docs table, skill note, CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: only the DETK-0047 set is accepted, no formula text reaches formulaic or R as an expression, the edge cases and provenance match DETK-0047, the R-gated tests in CI <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-19 on Adam's answer to DETK-0028 ("support a fixed set of
transforms in 1.0", the option reading "Support a small whitelist (log,
log2, etc.) in 1.0 and record it in provenance"). The set, the names, the
edge cases and the provenance are DETK-0047, Proposed and Adam's; this
node waits on it. Comes after release/formula-rename, which renames the
module this node edits, and after release/cli-migrate, which rewrites
`de.py`, `norm.py` and `transform.py`; this node's edits there are the
`params` keys only. The R quoting closes a path that exists today (a
column data column named like a call reaches R's `formula()` as a call),
which no working analysis depends on.
