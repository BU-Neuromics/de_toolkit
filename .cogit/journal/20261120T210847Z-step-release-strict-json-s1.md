---
kind: step
time: 2026-11-20T21:08:47Z
by: DETK/developer
node: release/strict-json
step: s1
branch: node/116-strict-json
verdict: done
commits: [95e0f0c, 893c30f, d790e2f]
decisions: []
---

# Done: Write non-finite numbers as null in the module JSON encoder and the crate, refuse bare NaN/Infinity at serialization, allow null in module_schema.json where needed, keep the views rendering nulls; the strict-parse test over every module's JSON and the crate (R-backed modules in the R job); CHANGELOG; open the PR

## Summary

Done: non-finite numbers written as null in module JSON (encode and iterencode paths, allow_nan=False forced) and the crate (finite_json); schema descriptions say null; views read null as missing (report_specs color scale, static scatter pairing — two files outside the listed scope, needed for the views acceptance); tests/report/test_strict_json.py runs every module-JSON subcommand (R ones in the R job) and strict-parses json/*.json, the crate and the payloads, validates the schema, re-renders an old bare-NaN report dir; jsdom render test with nulls; CHANGELOG under Fixed. PR #120, CI green incl. R on d790e2f. Found: detk-outlier entropy fails on an all-zero row (outlier.py:307, pandas 3), not fixed here.

## Artifacts

## Findings

## Questions
