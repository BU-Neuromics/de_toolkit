---
kind: task
objective: The published example report and crate under docs/example/ are regenerated with relative paths, and a test keeps any absolute path from the build machine out of them (Adam, 2026-11-20)
acceptance:
  - docs/example/detk_report.html and docs/example/ro-crate-metadata.json are regenerated, the way release/tutorial-airway publishes them, from a run on main with release/report-paths, release/tutorial-airway and release/outlier-entropy merged; the crate sits beside the report as DETK-0280 places it and docs/example.md's links to both resolve; mkdocs build --strict passes
  - 'a test reads every file under docs/example/ (the report''s embedded module JSON, the crate and the raw text) and fails on any absolute path: a value of workdir, argv or a file path field (in_file_path(s), out_file_path(s), column_data_path, a crate File @id) that is absolute or a file:// URI, and any raw occurrence of /home/, /Users/, /tmp/, /private/, /root/, a Windows drive path or file:// in the text; it passes on the regenerated files and fails on the files as published at 61bf890 (checked in the PR)'
  - 'the comment at tests/formula/test_formula_pins.py (about line 206) no longer names examples/airway/prepare_data.R or run.sh once release/tutorial-airway has retired them: it names where the airway sample sheet now comes from (the tutorial''s data step); CHANGELOG under Fixed (the published example''s machine paths)'
from: [DETK-0280]
scope: [docs/example/, +docs/example.md, new:tests/report/test_example_paths.py, +tests/formula/test_formula_pins.py, +CHANGELOG]
prev: [release/report-paths, release/tutorial-airway, release/outlier-entropy, release/cli-messages]
---

# The published example holds no machine paths

## Implementation plan

- [ ] @developer Regenerate docs/example/ from the airway tutorial's run on main, add the test that no absolute path appears in it (shown failing on the old files), fix the stale prepare_data.R comment in test_formula_pins.py; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: open docs/example/detk_report.html and the crate, grep them for absolute paths, run the new test against the old files from 61bf890, and confirm the R job ran the tutorial <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-21 on Adam's decision of 2026-11-20: the absolute machine
paths in the published example go before 1.0. On main at 61bf890,
docs/example/detk_report.html holds `"workdir": "/home/.../examples/airway"`
twelve times and `argv[0]` as `/home/.../.venv/bin/detk-<tool>` eight times;
the crate holds none. release/report-paths removes them at the source; this
node regenerates the published files and adds the guard.

Ordering: after release/report-paths (the source fix), and after
release/tutorial-airway (#117, which regenerates docs/example/ from the
tutorial and owns that directory until it merges) and
release/outlier-entropy (#125, which changes the entropy values the
example's outlier card shows). Regenerating needs R with DESeq2 and the
airway data, as release/tutorial-airway's run does; if that run is only
possible in the R job, the developer takes the files from the job's
artifacts the way release/tutorial-airway does.

Folded in: the stale comment at tests/formula/test_formula_pins.py:206,
which names examples/airway/prepare_data.R (retired by
release/tutorial-airway). That file is also in release/cli-messages'
scope (`tests/formula/`, in progress), so this node comes after both.
Before release/cli-docs (which owns docs/example.md's prose beside this
node's `+` entry) and release/cut.
