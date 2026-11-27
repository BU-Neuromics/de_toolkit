---
kind: task
objective: one command (where DETK-0602 puts it) checks counts, sample information, design and method before any fit and prints stable JSON diagnostics, each with a plain-language fix
acceptance:
  - 'reproduced first as tests from the audit''s cases, each passing a 1.0 check today and failing later: detk-wrapr check exits 0 with R and jsonlite while DESeq2 and logistf are missing; the sparse table (gene,A,B,C,D / 001,10,10,0,0 / 002,0,0,20,20) passes ''detk-filter nonzero(all) >= 0.5'' whole and then ''detk-norm deseq2'' exits 1 (every gene has a zero). After: the preflight reports the missing package for the requested method and that size factors cannot be computed, with the fix, exit 1'
  - it also reports the count checks (DETK-0601), sample-set agreement (DETK-0600) and the design's rank; the JSON is documented and versioned like the module JSON; the skill runs it before the analysis
from: [DETK-0602]
scope: [de_toolkit/preflight.py, tests/preflight/, +de_toolkit/wrapr.py, +docs/, +skills/detk/, +CHANGELOG]
---

# A JSON preflight before a fit

## Implementation plan

## Notes
