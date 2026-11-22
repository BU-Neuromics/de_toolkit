---
kind: task
objective: detk-outlier entropy runs on any counts matrix, including one with all-zero features, and every entropy value and flag is written on the row of the feature it was computed for
acceptance:
  - 'a counts matrix with an all-zero feature (first, in the middle and last, and several of them) runs without error (today: ''Series.replace cannot specify both a dict-like to_replace and a value'' from dropped_df.replace in EntropyCounts); the all-zero features get a missing entropy (empty in the CSV; how the module JSON writes a missing number is release/strict-json''s) and entropy_p0_XX False, with one warning giving how many; the percentile is taken over the non-zero features as today'
  - the output rows are aligned to the input by feature name, not by position (today results_df.index = counts_obj.counts.index relabels the concatenation [non-zero, all-zero] positionally, so every feature after an all-zero one gets another feature's entropy); the output keeps the input's row order; a test with an all-zero feature in the middle checks each row's entropy against scipy.stats.entropy of that feature's counts, and a test checks the output index equals the input index
  - '-p is a fraction (DETK-0200 Option A, added to this node by the driver under Adam''s delegation, 2026-11-20): numpy gets the threshold times 100, so -p 0.05 is the 5th percentile, and a -p not strictly between 0 and 1 is a ValueError in the API and a usage error (exit 2) on the CLI; tests in tests/outlier/ through the Python API and the CLI; CHANGELOG under Fixed'
  - 'the outlier report card draws its threshold rule at threshold x 100 on the 0-99 feature-percentile axis, and tests/report/test_report_render.py records the fraction and catches a 100x error; the flag column is named from the threshold''s full decimal digits, at least two (0.05 entropy_p0_05, 0.1 and 0.10 entropy_p0_10, 1e-05 entropy_p0_00001), so no value in (0, 1) fails on it, with a test and a CHANGELOG line under Fixed (scope extended under Adam''s delegation via the driver session, 2026-11-20, after the s2 review: a direct consequence of the DETK-0200 -p change)'
  - 'docs/tutorials/airway.md checks the flagged-gene count of the 5th percentile (925, was 13), verified by the R CI job that runs the page; regenerating docs/example/ is moved to release/example-paths, which regenerates it after release/report-paths and waits on this node (Adam''s delegation via the driver session, 2026-11-20)'
scope: [+de_toolkit/outlier.py, tests/outlier/, +CHANGELOG, +docs/tutorials/airway.md, +de_toolkit/report_specs.py, +tests/report/test_report_render.py]
issue: 123
visited: 8628a94
status: done
done: 7a61e4a
---

# detk-outlier entropy handles all-zero features and keeps each result on its feature

## Implementation plan

- [x] @developer Replace the dropped_df.replace line and the positional relabel in EntropyCounts with a reindex by feature name; all-zero features get a missing entropy and a False flag with one warning; tests with all-zero features first, in the middle and last, each row checked against scipy.stats.entropy, through the API and the CLI; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: run detk-outlier entropy on a counts file with an all-zero gene in the middle and check a few genes after it against their own entropies <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 from the release/strict-json session (#120) and
DETK-0200's context (release/tutorial-airway, #117). Priority: it may give
silently wrong results, so it has no prev and is ready now.

In `EntropyCounts.__init__` (`de_toolkit/outlier.py`, about line 307):
`dropped_df.replace(dropped_df, "Null")` raises under pandas 3 whenever a
feature is all zero, so the command fails on any unfiltered counts matrix.
Past it, `pd.concat([results_df, dropped_df])` orders the rows
[non-zero features, all-zero features], and `results_df.index =
counts_obj.counts.index` then relabels them by position: every feature
after the first all-zero one would get another feature's entropy and flag.
The crash hides the mislabelling today; fixing only the crash would expose
it, so both go in one change. If the replace line passed under the older
pandas that 0.x ran on, 0.x runs with an all-zero feature before the last row
wrote shifted results; the developer checks, and the CHANGELOG says so if so.

All-zero features: entropy is undefined, so it is written missing and the
feature is not flagged (flagging is for low entropy). Within DETK-0063, no
decision needed.

Kept out: what `-p 0.05` means (numpy's percentile takes a percent), which
DETK-0200 decides on release/tutorial-airway; its fix belongs to a node of
its own after this one, planned when DETK-0200 is answered. No open node
branch touches `outlier.py` or `tests/outlier/`. Before release/cut.

Amended 2026-11-20 (Adam's delegation via the driver session): DETK-0200
Option A (-p as a fraction) was added to this node, with the airway
tutorial's flagged-gene count; the regeneration of docs/example/ that
DETK-0200 records moved to release/example-paths, which regenerates the
example after release/report-paths and already waits on this node.
