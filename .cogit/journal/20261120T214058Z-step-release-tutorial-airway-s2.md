---
kind: step
time: 2026-11-20T21:40:58Z
by: DETK/reviewer
node: release/tutorial-airway
step: s2
branch: review/tutorial-airway
verdict: approve
commits: []
decisions: []
---


# Approved: the airway tutorial reads well as user docs, the run is tested, and the R job ran it

## Summary

docs/tutorials/airway.md meets every acceptance item. I followed it as a new user would. Its checked outputs agree with the published report and crate. test_airway.py compares detk against DESeq2 run directly in R: results to rtol 1e-6 (baseMean 1e-8), size factors to 1e-10. The R job ran the page with DETK_TUTORIALS_REQUIRE_ALL=1 at 43616dc. Nothing blocks approval.

## Artifacts

- CI run 44813465796 (43616dc): test with R (bioconda) green

## Findings

- **R job (43616dc, run 44813465796): green.** `test with R (bioconda)` ran 2304 tests: 2304 passed, 22 skipped. `tests/tutorials/test_tutorials.py` passed 2 with DETK_TUTORIALS_REQUIRE_ALL=1 (airway and quantifiers), and `tests/tutorials/test_airway.py` passed 4. The CI rerun on eeb97fe was still running when I recorded this. eeb97fe changes only `.cogit/` (DETK-0200 accepted), so its result does not affect this review.
- **The page as user docs.** It covers the data from the airway package, stats summary, filter, `norm deseq2 --size-factors`, vst, outlier entropy, `de deseq2 "counts ~ cell + dex[untrt]"`, annotate with symbols, the report and the crate. Its checked outputs are the 24706 filtered genes, the size factors, the top ten genes with symbols, the result columns and the crate's step list. The fgsea step is shown but not run, which matches the node's notes. The writing is clear and explains why `norm_counts.csv` is not passed to detk-de.
- **The page against the published report and crate.** I checked docs/example/: the report's `num_kept` is 24706. Its size factors (1.024, 0.896, 1.179, 0.670, 1.178, 1.399, 0.921, 0.945) are the page's values rounded. The crate has the same 12 `detk-* run` actions as the page's expected list, with no workdir paths.
- **The test is meaningful.** It runs DESeq2 directly on the page's own counts_filtered.csv and sample_info.csv with `relevel(dex, "untrt")`, design `~ cell + dex`, `independentFiltering = FALSE` and `cooksCutoff = FALSE`. That matches what detk reports. It also checks that annotate adds the symbol and changes nothing else.
- **The commands exist once.** run.sh only runs the page through pytest and copies the report and crate. tests/example/ and prepare_data.R are removed. docs/example.md links the tutorial. The skill's airway.md has `--size-factors` again, and its R script is identical to the page's. `test_airway_reference_follows_the_tutorial` passes, and so does DETK-0070's skill test.
- **Local checks.** `pytest tests/skills tests/tutorials`: 55 passed, 6 skipped (the R-gated tests). `docs build (strict)`, ruff and runtime-deps pass in CI. CodeQL fails only on the two known alerts in the bundled Vega-Lite inside docs/example/detk_report.html, #8 and #9 (js/incomplete-sanitization), which are also open on main. They go to Adam and are not counted against the PR.
- **Known:** the `13` flagged genes check will change when release/outlier-entropy fixes DETK-0200, now Accepted.
- **Nits, not blocking:**
  - `tests/formula/test_formula_pins.py:207`: a comment still names the removed `examples/airway/run.sh` copy and `examples/airway/prepare_data.R`. The file is outside this node's scope, so this is a follow-up.
  - The page runs `Rscript prepare_data.R 2> /dev/null`. If a user is missing a package, that hides the R error.
- **For Adam, pre-existing and not from this PR:** the published report embeds the absolute local paths of the machine that made it, in each module's `argv[0]` and `workdir`. This time that is `/home/adamlabadorf/de_toolkit/.claude/worktrees/...`; main's copy has `/home/labadorf/...`. Consider having report metadata record paths relative to the workdir, or strip the `argv[0]` directory, before 1.0. The published report also no longer has the fgsea section. The page says so.

## Questions

None.
