---
kind: step
time: 2026-11-27T19:03:45Z
by: DETK/developer
node: release-1-0-1/fgsea-statcol
step: s1
branch: node/180-fgsea-statcol
verdict: done
commits: [cb82fa7, eb4c955]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Reproduction test (no R) fails on v1.0.0's enrich.py (exit 0, ranks condition__treated__padj) and passes here: exit 2, usage + one line naming the 11 candidate columns and -c/--statcol, before FGSEARes/R. One numeric column besides the ID ranks as before; module JSON params record statcol, idcol, ascending. Help, docs/tools/enrich.md, skill commands reference, CHANGELOG 1.0.1 Behaviour changes; zsh completion regenerated (generated from help, outside listed scope). PR #190.

## Artifacts

## Findings

## Questions
