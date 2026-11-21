---
kind: step
time: 2026-11-21T02:19:49Z
by: DETK/developer
node: release/report-paths
step: s1
branch: node/133-report-paths
verdict: done
commits: [1e59ba6]
decisions: []
---

# Done: As DETK-0280 is answered: write the crate into the report directory, rooted there; record workdir, argv[0] and the file paths relative as it says; the crate's references relative to its root; tests for two report directories, clean, the absence of machine paths and profile conformance; the docs, skill, tutorial and tests that name ./ro-crate-metadata.json; CHANGELOG; open the PR

## Summary

The crate is written into the report directory and rooted there (DETK-0280 Option A): File @ids relative to it (../counts.csv), no file:// URI; module JSON schema 1.2 records workdir relative to the report directory (.. by default), argv[0] as the command's name, and every file path relative to workdir (typed absolute too); detk-report clean removes the crate with the report directory and leaves an old ./ro-crate-metadata.json. New tests/report/test_report_paths.py (two report dirs, generate, clean, workdir .., absolute typed paths, no machine path with the report inside and outside the working directory); test_crate's absolute-URI test replaced by its relative counterpart plus an older-document test, profile validation rooted in the report dir with ../ refs (REQUIRED clean). Docs (report.md crate section and an optional-field table saying what each path is relative to), util.md, SKILL.md, agent-skills.md, references/airway.md, quantifiers and airway tutorials, run.sh, CHANGELOG under Changed. Decisions within the node: schema 1.2 (workdir's meaning changed; an absolute 1.0/1.1 workdir resolves the same way joined to the report dir, so the minor rule in docs/report.md now also covers such a change); argv[0] is os.path.basename(sys.argv[0]); DetkReport keeps crate_dir as an optional override; the 'stdout' output sentinel is still listed as a File, as before. Outside the scope, needed for the suite: docs/tutorials/airway.md and tests/tutorials/test_airway.py (tutorial-airway merged and moved the crate grep there), tests/report/test_strict_json.py (looked for ./ro-crate-metadata.json), de_toolkit/completions/detk.zsh (regenerated: it embeds clean's help). ruff, full pytest (2408 passed after merging main) and mkdocs --strict pass; the airway tutorial skips locally without R.

## Artifacts

## Findings

## Questions
