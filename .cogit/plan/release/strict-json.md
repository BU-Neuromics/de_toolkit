---
kind: task
objective: 'Every module JSON document, the report''s embedded payload and the Process Run Crate are strictly valid JSON: no bare NaN or Infinity, a missing or non-finite number written as null'
acceptance:
  - the report's JSON encoder (NumpyEncoder in de_toolkit/report.py, which today writes a float NaN as the bare token NaN and inf as inf) writes NaN, inf and -inf as null, at every nesting level, for Python floats, numpy floats and values inside arrays and DataFrame-derived lists; module JSON is serialized with allow_nan=False semantics so a non-finite value can never be written bare again; ro-crate-metadata.json (de_toolkit/crate.py) likewise
  - a test runs every detk module that writes a module JSON (each subcommand of detk-stats, detk-norm, detk-transform, detk-filter, detk-outlier, detk-de, detk-enrich, detk-util, the R-backed ones in the R job) on fixture data that yields missing values where the module can produce them (detk-stats summary --color-col with a missing color value, pca, rowzero), then parses every json/*.json and the crate with a strict parser (json.loads with parse_constant raising on NaN/Infinity) and validates each module JSON against module_schema.json; the schema allows null where a number may be missing
  - the HTML report still renders the views of modules with null values (the charts skip or show them as missing, the static fallback too), checked in the render tests; detk-report re-renders a report directory written by 0.x or earlier main (bare NaN in module JSON) without failing; CHANGELOG under Fixed
scope: [+de_toolkit/report.py, +de_toolkit/crate.py, +de_toolkit/module_schema.json, de_toolkit/templates/, tests/report/, +CHANGELOG]
prev: [release/record, release/help-options]
issue: 116
visited: 118283e
status: done
done: 08f461e
---

# Module JSON is strictly valid JSON

## Implementation plan

- [x] @developer Write non-finite numbers as null in the module JSON encoder and the crate, refuse bare NaN/Infinity at serialization, allow null in module_schema.json where needed, keep the views rendering nulls; the strict-parse test over every module's JSON and the crate (R-backed modules in the R job); CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: parse a real report directory's json/*.json with a strict parser (e.g. jq or Python with parse_constant), open the report with missing values <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 at the driver's request (item 8 of the follow-ups):
module JSON documents can hold bare `NaN`, which is not JSON; agents and
strict parsers (jq, JSON.parse, most non-Python readers) reject the file.
Seen with a missing value under `detk-stats summary --color-col`
(release/help-options) and in the existing PCA and rowzero outputs. The
cause is `NumpyEncoder.encode` in `report.py`, which formats every float
with `.3f` and turns `nan` into `NaN` (and leaves `inf` as `inf`).
null is what JSON has for a missing number, and what the schema and the
views can be taught to read; no decision is needed (within DETK-0063).
Reading old report directories with bare NaN back stays possible, since
Python's json reads them.

After release/record (which edits `report.py`, `crate.py` and
`module_schema.json`) and release/help-options (`report.py`, and the
`--color-col` output this must cover). Before release/cut.
