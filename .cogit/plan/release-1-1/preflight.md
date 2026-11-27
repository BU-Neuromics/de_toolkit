---
kind: task
objective: one command (where DETK-0602 puts it) checks counts, sample information, design and method before any fit and prints stable JSON diagnostics, each with a plain-language fix
acceptance:
  - 'reproduced first as tests from the audit''s cases, each passing a 1.0 check today and failing later: detk-wrapr check exits 0 with R and jsonlite while DESeq2 and logistf are missing; the sparse table (gene,A,B,C,D / 001,10,10,0,0 / 002,0,0,20,20) passes ''detk-filter nonzero(all) >= 0.5'' whole and then ''detk-norm deseq2'' exits 1 (every gene has a zero). After: the preflight reports the missing package for the requested method and that size factors cannot be computed, with the fix, exit 1'
  - it also reports the count checks (DETK-0601), sample-set agreement (DETK-0600) and the design's rank; the JSON is documented and versioned like the module JSON; the skill runs it before the analysis
from: [DETK-0602]
scope: [de_toolkit/, tests/, docs/, skills/detk/, +CHANGELOG]
prev: [features/wrapr-check-options, release-1-0-1/sample-match, release-1-0-1/count-checks-readers]
---

# A JSON preflight before a fit

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.1 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.1.0; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.1 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Adam's direction: "JSON preflight (samples, design rank, size-factor
feasibility)". The R-package half is the method-aware `detk-wrapr check` of
features/wrapr-check-options (#164); this node reuses it. Both audit cases
reproduced on main: `detk-wrapr check` exits 0 with an R lacking DESeq2 and
logistf; the sparse table passes the skill's filter whole and `detk-norm
deseq2` then exits 1 ("every gene contains at least one zero"), which is an
error, not a silent result, so it belongs to preflight rather than 1.0.1.
The scope's de_toolkit/preflight.py assumes DETK-0602's recommendation.
