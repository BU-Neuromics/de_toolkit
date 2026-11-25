---
kind: outcome
objective: 'detk 1.0.0 is released: tagged, on PyPI by Trusted Publishing, with a GitHub Release and a Zenodo DOI'
acceptance:
  - 'ready to cut: every criterion of the definition of done below holds on main (approved by Adam, 2026-11-23)'
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
- [ ] [detk-util record writes an existing path with spaces relative](release/record-space-paths.md) <!-- s56 -->
- [ ] [Cut 1.0.0](release/cut.md) <!-- s1 -->
- [ ] @human Accept: 1.0.0 is out <!-- s2 -->

## Definition of done

Approved by Adam on 2026-11-23 (his answer relayed by the driver session,
2026-11-23), as DETK-0063 item 1 asks: the record of the 1.0 bar. Criterion 3
is reworded from the draft because #23 (the roadmap) is not on the v1.0.0
milestone; criterion 34 is in, in the form Adam gave: 0 open Dependabot alerts.

1.0 is **ready to cut** when every criterion below holds on `main`. Each one
names how to check it. After that, the release itself (the tag, PyPI, the
GitHub Release and Zenodo) waits for Adam's go-ahead.

### A. The record

1. **Every node is done.** Every child of `release` except `release/cut`
   shows done in `cogit plan release --all`. That covers statsmodels-test,
   cli-migrate, formula-migrate, formula-rename, r-design-names,
   size-factors, cli-gaps, record, tutorial-harness, miller-recipes,
   tutorial-quant, tutorial-airway, tutorial-covariates and cli-docs, plus
   the 20 already done.
2. **Only DETK-0002 is still open.** No decision a release node follows
   from is Proposed, except DETK-0002 (`cogit decision list` shows nothing
   else waiting). Every decision accepted under the delegation is listed
   with its number in the cut PR's description, so Adam can veto any of
   them.
3. **The milestone is clear.** `gh issue list --milestone v1.0.0 --state open`
   shows only release-tracking issues: #20 (the cut sequence) and #22
   (DETK-0002) while it is open. The roadmap, #23, is not on the milestone
   and this criterion does not ask for it.

### B. CI on main's head

4. **Every check passes.** On the head of `main`, all of these are green:
   ruff, the ruff format check, the docs build (`mkdocs build --strict`),
   the tests on Python 3.11, 3.12 and 3.13, the R job (bioconda), the
   runtime-only import check, and combined coverage. Python 3.14 stays best
   effort (DETK-0019).
5. **The coverage floor holds.** Combined coverage passes `--fail-under=87`
   or higher, and the floor in `ci.yml` has not been lowered.
6. **The R job runs everything that needs R or Miller.** Its pytest report
   shows the R-gated tests, the Miller recipe tests and the R/Miller
   tutorials as *passed*, not skipped. Checked from the job's
   `-rs` skip summary, which lists no skipped test that names R, DESeq2,
   airway or mlr.

### C. The interface promise (DETK-0001 B, DETK-0023, DETK-0025 B)

7. **docopt-ng is gone.** `grep -ri docopt pyproject.toml uv.lock de_toolkit/`
   finds nothing, and every entry point uses argparse.
8. **Help keeps its promise.** The help-structure test passes for every
   command and subcommand: section order; every positional and option with
   its metavar, default, choices and description; at least one example per
   subcommand, which parses.
9. **The umbrella command is complete.** `detk <command>` runs every module
   command, and its usage lists them all.
10. **Command parsing is pinned.** The cli-pin suite (`tests/cli/`) passes,
    including the four DETK-0033 behaviours as parse errors.
11. **Exit codes are 0/2/1.** Success exits 0, a usage error 2 and anything
    else 1 (DETK-0031). The codes are pinned per class in cli-pin, stated in
    help epilogs, and documented in `docs/concepts.md` and the skill.
12. **Completion ships.** bash, zsh and tcsh completion scripts are in the
    wheel (DETK-0032). The regeneration test passes, shtab is not a runtime
    dependency, and `detk completion bash` works.

### D. Formulas (DETK-0024, DETK-0027, DETK-0040, DETK-0049, DETK-0050)

13. **patsy is gone.** No `de_toolkit` module imports patsy, and patsy is not
    a runtime dependency. formulaic builds the matrices, and the module is
    `de_toolkit/formula.py` with no `patsy_lite` name left (grep).
14. **Formula behaviour is pinned.** The formula-pin tests pass with the
    changes DETK-0040 and DETK-0049 made, and each change is named in the
    CHANGELOG. `detk-de deseq2` and `firth` give the same results on airway
    as before, checked by the R-gated tests.
15. **Formulas are model-only.** A term that looks like a call and is not a
    column raises `FormulaParseError` pointing to the derived-covariates
    recipes page. A column that is really named like a call still works.
    `docs/formulas.md` makes no `np.log` claim. All three are tested.
16. **R reads names safely.** Every design name that is not a syntactic R
    name is backtick-quoted before R's `formula()`. A test with a column
    named like a call shows R never runs it.

### E. The remaining CLI gaps and dependencies

17. **--column-data is gone.** A repository-wide search finds it only in the
    CHANGELOG's history (DETK-0030; `--column-data-output` is a different
    option). Its pins now expect exit 2.
18. **--size-factors works.** `detk-norm deseq2 --size-factors=FILE` writes
    the size factors, and a test checks them against DESeq2's (DETK-0029).
19. **statsmodels is test-only.** It is in the `test` extra and the `dev`
    group only. `environment.yml` does not exist, nothing in the repository
    refers to it, and the runtime-only check passes (DETK-0026, DETK-0048).

### F. Derived covariates (DETK-0050, DETK-0051 C, DETK-0061, DETK-0062)

20. **`detk-util record` works as DETK-0061 decides.** Its tests pass:
    refusals, exit codes, module JSON with checksums, the schema's optional
    fields, and a crate whose instrument is the external tool. A test shows
    a recorded step as the producer of a later `detk-de` run's column data.
21. **The Miller recipes are tested.** `docs/recipes/covariates.md` runs in
    the R job with mlr. That covers each recipe, each failure (non-zero
    exit, the samples named, no output file), values against numpy (n-1)
    and R's `scale()`, and IDs kept as written.
22. **The skill carries the recipes.** Its covariates reference matches the
    page (consistency test), and it warns that tidyr's `gather` means the
    opposite of `detk-util gather`.

### G. Tutorials (DETK-0064)

23. **Every tutorial is a test.** `docs/tutorials/` holds at least the
    quantifiers, airway and covariates tutorials, listed in its index and
    the nav. Each runs as a test under the harness, with its shown outputs
    checked.
24. **Each tutorial runs where it should.** The quantifiers tutorial runs in
    every test job. The airway and covariates tutorials run, and pass, in
    the R job (see 6).
25. **The airway commands exist once.** `docs/example.md` links the tutorial,
    and the published `docs/example/` report and crate come from the
    tutorial's run. No second copy of the commands is run by a test.

### H. Docs and skill

26. **Docs match the CLI.** Every usage block in `docs/tools/*.md` and
    `docs/report.md` matches the installed `--help`, checked by the docs
    usage test.
27. **The promise is written down.** `docs/index.md` and `docs/api.md` state
    what 1.0 promises about help (DETK-0025 B). No page describes docopt
    docstrings as the interface, and `docs/dev/` says how to add a command
    with argparse and how to write a tutorial.
28. **README and quickstart commands run.** They run as written on the 1.0
    CLI, checked by a test or by being tutorial pages.
29. **The skill matches the CLI.** DETK-0010's skill test passes against the
    argparse parsers, and the skill states the exit codes.
30. **What shipped in 1.0 is documented.** TPM and CPM (#24), annotate
    (#29), gather (#25), the agent skill (#38), `detk-util record` and the
    tutorials each have a docs page in the nav.

### I. Packaging and the release candidate

31. **The wheel is clean.** `uv build` makes an sdist and a wheel, and
    `twine check dist/*` passes. Installing the wheel into a fresh venv with
    runtime dependencies only lets every entry point's `--help` exit 0.
32. **The CHANGELOG says what breaks.** Its 1.0.0 section has a "Breaking
    changes from 0.9" list naming: argparse and its metavar changes, exit
    codes 0/2/1, `--column-data` removed, the patsy-to-formulaic changes
    (column order with interactions, error messages, model-only formulas),
    statsmodels and patsy no longer installed, `environment.yml` removed,
    and Python 3.10 dropped. Checked by the reviewer of the version-bump
    PR against this list.
33. **The version-bump PR is ready.** `release/cut` step s2's PR is open,
    reviewed and green: `version.py` at 1.0.0, the Production/Stable
    classifier, and the CHANGELOG heading dated.

### J. Security

34. **No open security alert on the lockfile.**
    `gh api repos/BU-Neuromics/de_toolkit/dependabot/alerts?state=open`
    lists no alert: 0 open Dependabot alerts (it held on 2026-11-23).

**Ready to cut** means 1–34 all hold. The work then stops at Adam's steps
on `release/cut`:

- s1: confirm PyPI Trusted Publishing and Zenodo.
- s7: answer DETK-0002 (answered 2026-11-23: leave the data in history).
- s3: accept the PR and give the go-ahead.

Only after that does a session push the tag, create the GitHub Release,
and check PyPI and the DOI (s4–s5). Adam then accepts (s6, then release
s2). The acceptance above stays as the post-release check:
`pip install de_toolkit` installs 1.0.0, the tag, Release and DOI exist,
and the README shows the DOI.

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
