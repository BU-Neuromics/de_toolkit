---
kind: task
objective: 'No column data name reaches R''s formula() as code: every name in the resolved design that is not a syntactic R name is backtick-quoted before R reads it (DETK-0050)'
acceptance:
  - 'the formula module gives the R-bound form of the resolved design, in which every name R would not read as a plain name (make.names(x) != x, or a reserved word) is backtick-quoted, with backticks inside a name escaped; every R site that calls formula() on a detk design uses it: detk-de deseq2 and firth (de.py), detk-transform rlog and vst (transform.py), and detk-norm deseq2 where it passes a design (norm.py)'
  - 'a test with a column data column named like a call (e.g. `print(1)` or `system("true")`, created in a temp file) shows the R-backed commands treat it as a column name and run no code, R-gated in CI; a column named with dots (`fld.cont`, issue #34''s case) still works unquoted'
  - 'params.design in the module JSON and the crate keeps the unquoted resolved design, as today; results and matrix column names are unchanged; the formula-pin and de tests pass unchanged'
  - 'the CHANGELOG notes the fix'
from: [DETK-0050]
scope: [+de_toolkit/formula.py, +de_toolkit/de.py, +de_toolkit/transform.py, +de_toolkit/norm.py, tests/de/, tests/transform/, +CHANGELOG]
prev: [DETK-0050, release/formula-rename, release/cli-migrate]
issue: 94
visited: b760aac
---

# Quote design names before R reads them

## Implementation plan

- [ ] @developer Add the R-bound design form with quoting to the formula module, use it at every R `formula()` site, add the call-shaped-name tests (R-gated) and the dotted-name regression test; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: every R site covered, nothing in a column data file can run R code through the design, the R-gated tests in CI <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-19. The issue came up in DETK-0047 item 5 and is kept when
DETK-0050 drops transforms. Today the lexer accepts `(`, `)`, `.` and `:` in
names, and the resolved design goes to R's `formula()` unquoted, so a
column data name such as `system("...")` would be run by R when the model
frame is built. No working analysis depends on that: such a design fails
in R today. Adam has not ruled on this explicitly. The planning session
recommends it as a fix with no decision record: it removes a code
execution path and changes no working behaviour. He sees it when he
accepts this node's PR. Comes after release/formula-rename (the module's
new name) and release/cli-migrate (which rewrites de.py, norm.py and
transform.py).
