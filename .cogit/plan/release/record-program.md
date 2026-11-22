---
kind: task
objective: 'As DETK-0390 is answered (recommended Option B): detk-util record writes the program of the step it records, typed as an absolute path, as its bare name when PATH finds that same file by that name, as detk''s own argv[0] is its name, instead of a ../ chain whose depth is the working directory''s'
acceptance:
  - 'under DETK-0390 Option B: detk-util record -- /usr/bin/cp a b (or the absolute path shutil.which gives for a program on PATH) writes argv with cp as the program in the module JSON, the embedded report payload and the crate; a program PATH does not find under that name, or finds as another file, is written relative to workdir as today; the rest of argv, params and properties are unchanged; tests in tests/util/test_record.py for both cases and for a bare name typed as such'
  - the recorded command line re-runs from workdir (a test runs the recorded argv and gets the same output); module_schema.json's argv description and record's help (if it describes argv) say the rule; CHANGELOG under Changed. Under Option A this node is closed as not planned and release/cli-docs carries the note
from: [DETK-0390]
scope: [+de_toolkit/util.py, +de_toolkit/report.py, +de_toolkit/module_schema.json, +tests/util/test_record.py, +CHANGELOG]
prev: [DETK-0390, release/recipe-notes]
---

# detk-util record writes a program PATH finds by its name

## Implementation plan

- [ ] @developer As DETK-0390 is answered: write record's absolute program as its name when PATH finds the same file, otherwise relative as today; tests, schema description, CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: from a working directory deep in another tree run detk-util record -- /usr/bin/cp a b and one with a program off PATH, read argv in the module JSON and the crate, and re-run the recorded line <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-22 from the release/report-paths review (#134, not
blocking): since DETK-0281 every absolute path typed on record's command
line is written relative to `workdir`, so `detk-util record --
/usr/bin/cp a b` is recorded as `../../../../../../usr/bin/cp`, a form
whose depth is the working directory's and which stops re-running if the
project moves. Whether 1.0 changes this, or only documents it, is
DETK-0390 (Proposed, recommending Option B: the program by name when PATH
finds the same file; `workdir`'s `../` chain documented only, in
release/cli-docs). Under Option A this node is closed as not planned.

After DETK-0390 and release/recipe-notes (in progress), which edits
`run_record` in `util.py` (the command text of its failure messages) and
tests/util/test_record.py. Before release/cli-docs (which documents the
rule) and release/cut.
