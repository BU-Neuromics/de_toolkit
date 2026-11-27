---
kind: task
objective: 'detk-wrapr check lists only its own options and checks the R packages each detk method needs (tracks #164)'
acceptance:
  - detk-wrapr check --help lists --rpath and the logging and --version options only; --meta-in, --params-out, --strict, --routput-dir, -d and --report-dir are not accepted by check; the docs usage block and tests/docs/test_docs_usage.py follow; CHANGELOG
  - 'method-aware (folded in 2026-11-27 from the AI-readiness audit, Adam''s direction): reproduced first as a test with a stub Rscript, on v1.0.0 check exits 0 with R and jsonlite while DESeq2 and logistf are missing. After: check lists each R package a detk method uses (DESeq2, logistf, fgsea; BiocParallel optional) as found or missing, and asked about a method (an added option, its name this node''s call) exits 1 naming the missing package and how to install it; without one it keeps 1.0''s exit status'
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

Widened 2026-11-27 by the plan session on Adam's direction via the driver
session ("fold a method-aware detk-wrapr check into #164"): the audit found
`detk-wrapr check` succeeding with DESeq2 and logistf missing, reproduced on
main with an R that lacks them. It adds an option, so it stays after 1.0.1;
`release-1-1/preflight` builds on it.
