---
kind: step
time: 2026-11-20T21:28:44Z
by: DETK/reviewer
node: release/strict-json
step: s2
branch: review/strict-json
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: parse a real report directory's json/*.json with a strict parser (e.g. jq or Python with parse_constant), open the report with missing values

## Summary

Approved at 966287b: module JSON, payloads and crate strict (encoder paths probed, real report dir strict-parsed, jsdom render ok); old bare-NaN dir from main re-renders; R strict test ran in the R job (57/57 dots, no skip); out-of-scope view edits needed and minimal; CI green incl. R. Non-blocking: jq accepts NaN, jsdom tests not in CI.

## Artifacts

## Findings

Review of s2 at 966287b. Approved.

Checked: the diff origin/main...966287b (report.py, crate.py, module_schema.json, report_specs.py, static_plots.py, tests/report/test_strict_json.py, tests/report/test_report_view_text.py, CHANGELOG). PR #120 CI is green on 966287b: 3.11/3.12/3.13, docs-strict, runtime-only, ruff, CodeQL, and "test with R (bioconda)" (2356 passed, 23 skipped). Locally on 3.13 (uv, dev group), the full suite gives 2285 passed, 94 skipped (all R or jsdom).

The R-backed strict test ran in the R job. tests/report/test_strict_json.py collects 57 tests. In the R job's progress output, on d790e2f and again on 966287b, that file prints 39 + 18 = 57 dots and no `s`, so test_every_r_module_writes_strict_json (vst, rlog, deseq2, firth, fgsea) ran and passed. The ~60 s gap on that line fits the R modules running. Locally, without R, it is the file's one skip.

Encoder: NumpyEncoder forces allow_nan=False and sends every path through finite_json: encode for floats, lists and mappings, and iterencode for json.dump and for anything else json.dumps hands down. I probed it by hand with json.dumps (with and without indent) and with json.dump. Python NaN/inf/-inf, np.float16/32/64/longdouble, nested ndarrays, DataFrame.to_dict('records'), Series.values, and numpy ints and bools all come out as null or as plain Python values, and every result strict-parses. The crate: finite_json plus allow_nan=False in write_crate and in the PropertyValue json.dumps; a raw float param that is NaN passes the isinstance check and is nulled at write.

A real report directory (summary --color-col with a missing batch value, rowzero with an all-zero row, basestats, cpm) gives 7 module JSON files and a crate. All 8 strict-parse (Python, parse_constant raising), with no NaN or Infinity token anywhere. Both embedded payloads (detk-modules, detk-raw) strict-parse. Rendered in jsdom (tests/report/render_dom.js), every card builds its view, with no alerts.

Old report directories: I built one with origin/main's code (4 module JSON files with bare NaN) and ran `detk-report generate` with this branch. It re-renders, the new payloads and the crate are strict, and every card renders in jsdom.

Render tests: the jsdom tests in test_report_view_text.py skip in every CI job, as on main, because CI has no node+jsdom. I ran them locally with jsdom 25.0.1 on NODE_PATH: 12 passed, including the new test_views_with_null_values_render. The static fallback (test_static_fallback_skips_null_points) and view compilation (test_views_with_nulls_compile) run in CI.

Edits outside the listed scope: report_specs.py `_color_by` and static_plots.py `scatter_svg`. Both are needed for the acceptance's "views render nulls", and both are minimal. Before the change, a single null in a numeric color column made it nominal. Separately, a null x or y made the static scatter's xs and ys lists different lengths: matplotlib errors on that, or worse, pairs the wrong points. They are view code in the same layer as templates/. I judge them in bounds, and no decision is needed.

CHANGELOG under Fixed, accurate.

Not blocking:
1. jq (1.7 and later; 1.8.2 here) accepts a bare NaN and reads it as null, so `jq .` is not a strict check. The test rightly uses json.loads with parse_constant. The s2 step text's "e.g. jq" would pass the old files too.
2. The jsdom render tests never run in CI, including this node's null-rendering test. Adding node+jsdom to one CI job would cover them. That would be a follow-up outside this node.
3. Existing behaviour, not changed here: NumpyEncoder.encode, the json.dumps path, rounds floats to 3 decimals (`.3f`). That path builds the report's embedded payload (to_script_json) and param_str. The module JSON files on disk are written with json.dump (iterencode) and keep full precision. Noted for completeness, not for this node.

## Questions
