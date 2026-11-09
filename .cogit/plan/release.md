---
kind: outcome
objective: 'detk 1.0.0 is released: tagged, on PyPI by Trusted Publishing, with a GitHub Release and a Zenodo DOI'
acceptance:
  - pip install de_toolkit installs 1.0.0
  - the v1.0.0 tag and GitHub Release exist, and Zenodo has minted a concept DOI shown in the README
  - TPM and CPM (#24), result annotation (#29), gathering quantifier outputs (#25) and agent skills ship in 1.0
  - the interface promise of 1.0 (#18) and the history question (#22) are decided and recorded
issue: 23
visited: f6503ed
---

# Release 1.0.0

## Implementation plan

- [x] [Coverage floor](release/coverage.md) <!-- s3 -->
- [x] [Citation and release machinery](release/citation.md) <!-- s4 -->
- [x] [Airway worked example](release/example.md) <!-- s5 -->
- [x] [Schema docs](release/docs.md) <!-- s6 -->
- [ ] [TPM and CPM normalization](release/tpm-cpm.md) <!-- s7 -->
- [ ] [Annotate results with feature metadata](release/annotate.md) <!-- s8 -->
- [ ] [Gather quantifier outputs into a counts matrix](release/gather.md) <!-- s9 -->
- [ ] [Agent skills](release/agent-skills.md) <!-- s10 -->
- [ ] [Correct the FPKM formula](release/fpkm.md) <!-- s11 -->
- [ ] [Escape the module JSON in the report](release/escape-json.md) <!-- s12 -->
- [ ] [Read feature IDs as text](release/padded-ids.md) <!-- s13 -->
- [ ] [Read single-column files](release/single-column.md) <!-- s14 -->
- [ ] [Update locked dependencies](release/deps.md) <!-- s15 -->
- [ ] [Cut 1.0.0](release/cut.md) <!-- s1 -->
- [ ] @human Accept: 1.0.0 is out <!-- s2 -->

## Notes

Tracking issue #23 (the roadmap) and milestone v1.0.0. Two decisions gate the cut:
DETK-0001 (#18) and DETK-0002 (#22), both Proposed and Adam's. Adam promoted #24, #29
and #25 into 1.0 and added agent skills (2026-11-09); the other candidates wait in `features`.
