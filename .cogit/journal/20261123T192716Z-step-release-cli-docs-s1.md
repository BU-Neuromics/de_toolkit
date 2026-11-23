---
kind: step
time: 2026-11-23T19:27:16Z
by: DETK/developer
node: release/cli-docs
step: s1
branch: node/162-cli-docs
verdict: done
commits: [fd27897, 9d53376, 604a5f0, 8cca5e3, dc4c0ed, 8d8f793, b11044d]
decisions: []
---

# Done: Regenerate the usage blocks from `--help`, add the docs usage test, state the help promise, document exit codes and completion, rewrite what describes the docstring-as-interface pattern, add the how-to-add-a-command note, CHANGELOG; open the PR

## Summary

Usage blocks in docs/tools/ and docs/report.md regenerated from --help (usage, positionals, options) with tests/docs/docs_usage.py, and tests/docs/test_docs_usage.py checks each matches, every subcommand has one (wrapr check/run and report clean added), and the common-options block matches (record's no -d noted). Help promise (DETK-0025 B) on index.md and api.md; exit codes, completion and the ragged one-field header on concepts.md; docs/dev/cli.md on adding a command/option with argparse. report.md: quoted-argument exception (sh -c test in tests/docs), program by name incl. the /bin vs /usr/bin case (acceptance widened, DETK-0390), the ../ chain, stdout not a File, only record-checksummed files carry sha256/contentSize (crate.py docstring + test_crate.py test). agent-skills.md lists covariates.md, with a test. Doc bugs fixed: quickstart filter was inverted (nonzero(all) < 0.5 kept mostly-zero rows) and its fgsea statcol named no real column; de.md column name; wrapr run example was broken shell. A test runs the quickstart (R steps in the R job). Full suite 2593 passed, ruff clean, mkdocs --strict builds.

## Artifacts

## Findings

## Questions
