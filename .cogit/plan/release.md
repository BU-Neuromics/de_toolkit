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
- [ ] [Make statsmodels a test-only dependency](release/statsmodels-test.md) <!-- s27 -->
- [ ] [Replace docopt-ng in every command](release/cli-migrate.md) <!-- s23 -->
- [ ] [Replace patsy with formulaic in patsy-lite](release/formula-migrate.md) <!-- s24 -->
- [ ] [Rename patsy-lite to formula](release/formula-rename.md) <!-- s28 -->
- [ ] [Quote design names before R reads them](release/r-design-names.md) <!-- s31 -->
- [ ] [--size-factors writes the size factors](release/size-factors.md) <!-- s26 -->
- [ ] [Close the remaining CLI gaps](release/cli-gaps.md) <!-- s29 -->
- [ ] [Record an external step with detk-util record](release/record.md) <!-- s30 -->
- [ ] [Run tutorials as tests](release/tutorial-harness.md) <!-- s33 -->
- [ ] [Miller recipes for derived covariates](release/miller-recipes.md) <!-- s32 -->
- [ ] [Tutorial: from quantifier outputs to a normalized matrix](release/tutorial-quant.md) <!-- s34 -->
- [ ] [Tutorial: differential expression on airway](release/tutorial-airway.md) <!-- s35 -->
- [ ] [Tutorial: derived covariates and recorded steps](release/tutorial-covariates.md) <!-- s36 -->
- [ ] [Options do what their help says](release/help-options.md) <!-- s38 -->
- [ ] [Update the docs for the 1.0 CLI](release/cli-docs.md) <!-- s25 -->
- [ ] [Guard the removed dependencies and fix the E402 note](release/dep-guards.md) <!-- s37 -->
- [ ] [detk-util tidy writes the sample sheet as read and records in the report](release/tidy-output.md) <!-- s39 -->
- [ ] [Formula and filter errors are clear and never silent](release/parse-errors.md) <!-- s40 -->
- [ ] [Module JSON is strictly valid JSON](release/strict-json.md) <!-- s41 -->
- [ ] [detk-outlier entropy handles all-zero features and keeps each result on its feature](release/outlier-entropy.md) <!-- s42 -->
- [ ] [Design and filter commands say only what went wrong](release/cli-messages.md) <!-- s43 -->
- [ ] [detk-util record's help says what it does and lists only its options](release/record-help.md) <!-- s44 -->
- [ ] [The crate goes with its report and recorded paths are relative](release/report-paths.md) <!-- s45 -->
- [ ] [The published example holds no machine paths](release/example-paths.md) <!-- s46 -->
- [ ] [A one-field header over wider rows reads as R writes it](release/short-header.md) <!-- s47 -->
- [ ] [Recipe page notes and record's failure line](release/recipe-notes.md) <!-- s48 -->
- [ ] [CI runs the report's browser render tests](release/ci-jsdom.md) <!-- s49 -->
- [ ] [A sample sheet with ragged rows is an error, not one column](release/ragged-sheet.md) <!-- s50 -->
- [ ] [The render-test CI step reads only pytest's summary line](release/jsdom-summary.md) <!-- s51 -->
- [ ] [The crate does not list stdout as a file](release/crate-stdout.md) <!-- s52 -->
- [ ] [detk-util record writes a program PATH finds by its name](release/record-program.md) <!-- s53 -->
- [ ] [CI and release workflows run with least-privilege token permissions](release/workflow-permissions.md) <!-- s54 -->
- [ ] [detk-util tidy names a ragged sheet by the path it was given](release/tidy-sheet-name.md) <!-- s55 -->
- [ ] [Cut 1.0.0](release/cut.md) <!-- s1 -->
- [ ] [detk-util record writes an existing path with spaces relative](release/record-space-paths.md) <!-- s56 -->
- [ ] @human Accept: 1.0.0 is out <!-- s2 -->

## Notes

Tracking issue #23 (the roadmap) and milestone v1.0.0. DETK-0002 (#22), Proposed and
Adam's, deferred by him on 2026-11-20, is answered at release/cut's step s7. DETK-0001 (#18) was accepted on 2026-11-18 as option B: migrate off
docopt-ng and patsy before the tag. Adam then accepted argparse (DETK-0023), formulaic
(DETK-0024), help promised as DETK-0025 Option B with all the CLI gaps in 1.0, and
statsmodels as test-only (DETK-0026). On 2026-11-19 he also answered: formula.py
(DETK-0027), a fixed set of transforms in 1.0 (DETK-0028 Option B), implement --size-factors
(DETK-0029), remove --column-data (DETK-0030), exit codes 0/2/1 (DETK-0031), shtab at build
time (DETK-0032), delete environment.yml (DETK-0048), every deprecated --column-data
removed (his comment on DETK-0030) and model matrix columns in formulaic's order (DETK-0049).
He then changed his mind on transforms: formulas specify the model only, and a column data
augmentation command derives covariates (DETK-0050, superseding DETK-0028 and DETK-0047).
On 2026-11-20 he answered DETK-0051 with its Option C: no augmentation command; tested Miller
recipes in the docs and skill (release/miller-recipes, DETK-0062) and a `detk-util record`
command that records an external step (release/record, DETK-0061); the research is DETK-0060.
He asked for tutorials that are both docs and integration tests (DETK-0064: executable
Markdown run by pytest; release/tutorial-harness and three tutorial nodes), set how the
project runs toward 1.0 (DETK-0063: a definition of done he approves, delegated decisions,
plan PRs merged on green, the release his), and deferred DETK-0002, which is now a step of
release/cut rather than a gate on it.
release/size-factors moved here from features on 2026-11-19.
On 2026-11-20 Adam also decided that the absolute machine paths in the published example
(docs/example/) go before 1.0, fixed at the source: release/report-paths (with DETK-0280, where
the crate is written) and release/example-paths.
