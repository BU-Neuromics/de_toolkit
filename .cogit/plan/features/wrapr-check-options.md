---
kind: task
objective: 'detk-wrapr check --help lists only the options that act on check, not wrapr run''s (tracks #164)'
acceptance:
  - detk-wrapr check --help lists --rpath and the logging and --version options only; --meta-in, --params-out, --strict, --routput-dir, -d and --report-dir are not accepted by check; the docs usage block and tests/docs/test_docs_usage.py follow; CHANGELOG
scope: [de_toolkit/wrapr.py, +tests/, +docs/, +CHANGELOG]
---

# detk-wrapr check lists only its own options

## Implementation plan

- [ ] @developer Fix it with tests and a CHANGELOG entry; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-23 from the release/cli-docs review (#163, nits): `check`
shares `run`'s parser options, so its help lists options that do nothing for
it. The usage block is correct; the parser is at fault. After 1.0, not a
blocker (the reviewer's call, kept by the plan session).
