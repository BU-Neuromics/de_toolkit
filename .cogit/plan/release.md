---
kind: outcome
objective: 'detk 1.0.0 is released: tagged, on PyPI by Trusted Publishing, with a GitHub Release and a Zenodo DOI'
acceptance:
  - pip install de_toolkit installs 1.0.0
  - the v1.0.0 tag and GitHub Release exist, and Zenodo has minted a concept DOI shown in the README
  - TPM and CPM (#24), result annotation (#29), gathering quantifier outputs (#25) and agent skills ship in 1.0
  - the interface promise of 1.0 (#18) and the history question (#22) are decided and recorded
  - docopt-ng and patsy are replaced, the CLI unchanged for its users (DETK-0001 option B)
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
- [ ] [Render all view text as plain text](release/view-text.md) <!-- s16 -->
- [ ] [Bring the agent skill up to date](release/skill-update.md) <!-- s17 -->
- [ ] [Redraw the quickstart figure](release/quickstart-figure.md) <!-- s18 -->
- [ ] [Run the R tests on the locked environment](release/ci-lock.md) <!-- s19 -->
- [ ] [Keep IDs as written through R and the other readers](release/r-ids.md) <!-- s20 -->
- [ ] [Pin each command's parsing in tests](release/cli-pin.md) <!-- s21 -->
- [ ] [Pin the formula matrices in tests](release/formula-pin.md) <!-- s22 -->
- [ ] [Replace docopt-ng in every command](release/cli-migrate.md) <!-- s23 -->
- [ ] [Replace patsy in patsy-lite](release/formula-migrate.md) <!-- s24 -->
- [ ] [Update the docs for the migrated CLI](release/cli-docs.md) <!-- s25 -->
- [ ] [Cut 1.0.0](release/cut.md) <!-- s1 -->
- [ ] @human Accept: 1.0.0 is out <!-- s2 -->

## Notes

Tracking issue #23 (the roadmap) and milestone v1.0.0. DETK-0002 (#22), Proposed and
Adam's, gates the cut. DETK-0001 (#18) was accepted on 2026-11-18 as option B: migrate off
docopt-ng and patsy before the tag (cli-pin, formula-pin, cli-migrate, formula-migrate,
cli-docs); the migrations wait on DETK-0023 (parser) and DETK-0024 (formula library), Adam's. Adam promoted #24, #29
and #25 into 1.0 and added agent skills (2026-11-09); the other candidates wait in `features`.
