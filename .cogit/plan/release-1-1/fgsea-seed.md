---
kind: task
objective: detk-enrich fgsea --seed N makes a run repeatable, and the seed a run used is in its module JSON (DETK-0603)
acceptance:
  - 'reproduced first as a test: two identical ''detk-enrich fgsea -c condition__treated__stat'' runs on the audit''s table differ on v1.0.0 (NES 2.1317 and 2.1233 for ''up'', padj 0.000329 and 0.000329, background''s NES -1.6130 and -1.6103). After: the same --seed gives identical tables; the module JSON params hold the seed, as DETK-0603 settles for a run without --seed'
  - help, docs/tools/enrich.md, the skill's fgsea example and CHANGELOG 1.1
from: [DETK-0603]
scope: [de_toolkit/enrich.py, tests/enrich/, +docs/tools/enrich.md, skills/detk/, +CHANGELOG]
prev: [DETK-0603, release-1-0-1/fgsea-input]
---

# fgsea takes --seed and records it

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.1 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.1.0; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.1 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 before planning it; two
identical runs differed in NES and padj. Additive (DETK-0001): a new option.
