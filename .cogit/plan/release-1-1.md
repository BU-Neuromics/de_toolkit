---
kind: outcome
objective: 'detk 1.1 adds what makes a run easy to plan, inspect and replay: a fgsea seed, R and Bioconductor versions and optional checksums in the crate, a JSON preflight, and a release check of the published wheel'
acceptance:
  - fgsea takes --seed and records it; the crate names R and each Bioconductor package's version for the R-backed steps; checksums of inputs and outputs are recorded on request
  - a JSON preflight reports, before any fit, sample agreement, design rank, size-factor feasibility and the R packages the requested method needs, with a plain-language fix for each problem
  - release CI installs the published wheel and runs counts through to a validated crate with lineage assertions
  - 'every addition is additive under DETK-0001: no 1.0 command line changes meaning'
---

# Release 1.1: replayable, inspectable runs

## Implementation plan

- [ ] [fgsea takes --seed and records it](release-1-1/fgsea-seed.md) <!-- s1 -->
- [ ] [The crate names R and the Bioconductor package versions](release-1-1/crate-versions.md) <!-- s2 -->
- [ ] [Optional checksums of each step's files](release-1-1/crate-checksums.md) <!-- s3 -->
- [ ] [A JSON preflight before a fit](release-1-1/preflight.md) <!-- s4 -->
- [ ] [Release CI tests the published wheel from counts to a validated crate](release-1-1/wheel-ci.md) <!-- s5 -->
- [ ] [Cut 1.1.0](release-1-1/cut.md) <!-- s6 -->
- [ ] @human Accept: 1.1.0 is out <!-- s7 -->

## Notes

Planned 2026-11-27 by the plan session from the external AI-readiness audit
of 1.0.0 (Codex), on Adam's direction via the driver session: the additive
features. Nodes may start once the 1.0.1 nodes they follow are in; only the
cut waits for 1.0.1 to be out. The method-aware `detk-wrapr check`
(`features/wrapr-check-options`, #164) feeds `preflight`. Open questions:
DETK-0602 (where the preflight lives), DETK-0603 (fgsea with no --seed),
DETK-0604 (how checksums are asked for), each Proposed for the driver.
