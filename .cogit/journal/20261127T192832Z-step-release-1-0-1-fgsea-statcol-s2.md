---
kind: step
time: 2026-11-27T19:28:32Z
by: DETK/reviewer
node: release-1-0-1/fgsea-statcol
step: s2
branch: review/fgsea-statcol
verdict: approve
commits: []
decisions: [DETK-0760]
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: the reproduction test fails on v1.0.0's enrich.py and passes here; each acceptance criterion holds; CI green including the R job. The regenerated zsh completion is a mechanical consequence of the in-scope help change and acceptable. One out-of-scope doc (docs/tutorials/airway.md:352) still describes 1.0.0's behaviour: DETK-0760 Proposed.

## Artifacts

## Findings

- Reproduction: with v1.0.0's de_toolkit/enrich.py in place, test_fgsea_cli_ambiguous_statcol_is_usage_error fails (DID NOT RAISE SystemExit: 1.0.0 exits 0 ranking by the last numeric column, condition__treated__padj), as do test_read_result_stat_ambiguous and test_fgsea_cli_params_record_ranking[False/True]; all pass at b513339. The test uses an 11-numeric-column DESeq2-shaped fixture and a stand-in FGSEARes, so it needs no R and asserts FGSEARes was never called and no output written.
- AC1 holds: exit 2, the subcommand's usage and one 'error:' line naming every candidate column and -c/--statcol, raised in read_result_stat before FGSEARes. Checked by hand on a 3-numeric-column table: usage, "the results have 3 numeric columns that could be the ranking statistic (baseMean, a__stat, a__padj); name one with -c/--statcol", exit 2, no output file.
- AC2 holds: one numeric column besides the ID column (a text column alongside) ranks without -c; numeric columns are counted after -i (a numeric ID column named by -i is not a candidate).
- AC3 holds: params gain statcol, idcol (resolved names, also when -c/-i are 0-based indexes) and ascending, written to the module JSON (test reads it back); de_toolkit/module_schema.json unchanged, params is an open object. Series.abs() and negation keep the names, so -a/--abs do not lose them.
- AC4 holds: help's -c line, docs/tools/enrich.md (prose + help block), skills/detk/references/commands.md, CHANGELOG 1.0.1 "Behaviour changes" citing DETK-0600.
- Existing CLI tests that relied on the default now pass -c/--statcol explicitly; FakeFGSEARes in test_fgsea_cli_passes_ids_as_written gains a params dict. No weakened assertions.
- Scope: changes are within de_toolkit/enrich.py, tests/enrich/, docs/tools/enrich.md, skills/detk/references/commands.md, CHANGELOG, plus de_toolkit/completions/detk.zsh. The completion is generated from the help text (shtab) and tests/completion checks it is in sync; the two changed lines are exactly the new -c help string. Acceptable: a mechanical consequence of the in-scope help change, not a separate change. Suggest future nodes that touch help list it.
- Stale docs outside scope: docs/tutorials/airway.md:352-354 and skills/detk/SKILL.md:272 still say detk ranks by the last numeric column without -c. SKILL.md is in release-1-0-1/skill-guidance's scope and acceptance; the airway tutorial is in no node's scope: DETK-0760 (Proposed) recommends adding +docs/tutorials/airway.md to this node and fixing it in PR #190 before merge.
- Nit, not blocking: --abs also shapes the ranking but is not recorded in params; the acceptance names only statcol, idcol and ascending.
- Checks: local uv run pytest tests/enrich tests/cli tests/completion: 1695 passed, 28 skipped (R). CI on b513339 all green, including 'test with R (bioconda)': 2761 passed, 23 skipped, full suite with R.

## Questions

- DETK-0760 The airway tutorial's fgsea -c sentence after DETK-0600

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
