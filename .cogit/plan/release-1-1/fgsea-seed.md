---
kind: task
objective: detk-enrich fgsea --seed N makes a run repeatable, and the seed a run used is in its module JSON (DETK-0603)
acceptance:
  - 'reproduced first as a test: two identical ''detk-enrich fgsea -c condition__treated__stat'' runs on the audit''s table differ on v1.0.0 (NES 2.1317 and 2.1233 for ''up'', padj 0.000329 and 0.000329, background''s NES -1.6130 and -1.6103). After: the same --seed gives identical tables; the module JSON params hold the seed, as DETK-0603 settles for a run without --seed'
  - help, docs/tools/enrich.md, the skill's fgsea example and CHANGELOG 1.1
from: [DETK-0603]
scope: [de_toolkit/enrich.py, tests/enrich/, +docs/tools/enrich.md, +skills/detk/, +CHANGELOG]
---

# fgsea takes --seed and records it

## Implementation plan

## Notes
