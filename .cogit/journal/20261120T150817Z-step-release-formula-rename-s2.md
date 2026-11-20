---
kind: step
time: 2026-11-20T15:08:17Z
by: DETK/reviewer
node: release/formula-rename
step: s2
branch: review/formula-rename
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: nothing still names patsy-lite, the formula-pin fixtures unchanged but for names

## Summary

Approved: rename complete, pins unchanged but for names and the np.log message, call error per DETK-0050, airway column data verified against the airway package's sample table; CI green incl. R

## Artifacts

## Findings

- Rename complete: de_toolkit/formula.py, FormulaParseError (no alias), to_formulaic, tests/formula/; common.py imports the new module and says "detk formula syntax could not parse". `git grep -i 'patsy.lite\|patsy_lite\|patsylite'` outside .cogit finds only the CHANGELOG (the new entry naming the old names, and history).
- Pin fixtures: every pin and data file is a pure rename (git diff -M, 0 lines changed). test_formula_pins.py changes only the import, the exception name, docstring/comment wording, the new airway case, and the two np.log error cases' expected message (now `column names only.*np\.log\(cont\)`), as the acceptance allows.
- Call error (DETK-0050): checked in DesignMatrix against the column data; probed `a:log2(x)`, `log2(x)[A]`, `np.log(x):a`, `C(a)`, `I(x)`, LHS calls: all FormulaParseError naming the term and the column data file; a real column `age(yrs)` / `log2(cont)` / `np.log(x)[A]` still works. docs/formulas.md keeps interactions as the fourth term type and drops the np.log claim.
- Airway pin: tests/formula/data/airway.csv matches the airway Bioconductor package's inst/extdata/sample_table.csv (the source of colData(airway)) row for row (SRR1039508..SRR1039521; cell, dex), in the header and quoting prepare_data.R writes (sample,cell,dex; quote = FALSE). Pin values checked by hand (N052611 the reference, dex untrt the reference, counts zeros). The pin and its case pass on 7fbb940 (main's patsy_lite, parent 9adc1e4) and unchanged after the rename (pure rename of both files).
- Checks: `uv run pytest` 1987 passed, 76 skipped locally; PR #92 CI all green, including "test with R (bioconda)", ruff, docs build (strict), py3.11-3.13, coverage, CodeQL.
- Nit (no change asked): a misspelled column that contains parentheses, e.g. `age(yr)` for `age(yrs)`, now gets the call message rather than the unknown-column message; the message still names the term and says it is not a column of the column data file, so it is clear enough.

## Questions
