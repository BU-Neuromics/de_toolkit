---
kind: step
time: 2026-11-20T20:51:05Z
by: DETK/developer
node: release/miller-recipes
step: s1
branch: node/115-miller-recipes
verdict: done
commits: [667f6ea]
decisions: []
---

# Done: Write the recipes page as an executable tutorial page with each recipe and a failure, the numpy and R checks, the skill reference with its consistency test and the gather warning, Miller in the R job, the formula error's pointer and docs/formulas.md's link; CHANGELOG; open the PR

## Summary

Wrote docs/recipes/covariates.md as an executable tutorial page (requires mlr): a recipe per DETK-0062 operation (constant, _log2, _log10, _ln, _log2_pc1, _zscore n-1, _center, _minmax), each run through detk-util record with its output, plus one shown failure (missing + zero conc: exit 1, samples named, no file). Each recipe is a Miller program in a shell variable run as one 'mlr put -q -s col=... -s out=...' command (checks first, asserting_null to stop, emit > @out); the variable keeps every detk-util record line one shell line, which tests/skills' parser needs. Miller's stddev is one-pass (gives 1.2e-7 on six equal 7.2s), so the z-score computes mean and n-1 sd in two passes and finds no variance by min == max; non-numeric values (NA, text) fail like missing ones. tests/recipes: values vs numpy, vs R scale() in the R job, IDs as written, 22 failure cases on the page's own commands, module JSON naming mlr and its version, skill blocks on the page, the gather warning, the formula error's URL; skip without mlr, fail under DETK_TUTORIALS_REQUIRE_ALL. skills/detk/references/covariates.md + SKILL.md pointer and gather warning; formula error points to the page; docs/formulas.md link; nav; CHANGELOG. CI's R job already installs miller (tutorial-harness), so ci.yml is unchanged. Full suite passes locally with mlr 6.22 (R check skipped: no R locally).

## Artifacts

## Findings

## Questions
