---
kind: step
time: 2026-11-27T23:47:52Z
by: DETK/developer
node: release-1-0-1/outlier-entropy-p
step: s1
branch: node/222-outlier-entropy-p
verdict: done
commits: [e41ff43]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Reproduction tests (tests/outlier: no -p, and --help states the default) fail on v1.0.0 with 'argument -p/--percentile: invalid float value: None' (exit 2) and pass here. -p defaults to 0.05 (DETK-0860): same flags, column entropy_p0_05 and module JSON params as -p 0.05; stated in --help, docs/tools/outlier.md, skills/detk/references/commands.md; CLI table records the default; CHANGELOG 1.0.1 Fixed. -p given unchanged (DETK-0200 tests still pass).

## Artifacts

## Findings

## Questions
