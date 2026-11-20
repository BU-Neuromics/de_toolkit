---
kind: step
time: 2026-11-20T13:26:42Z
by: DETK/reviewer
node: release/formula-migrate
step: s2
branch: review/formula-migrate
verdict: approve
commits: []
decisions: []
---


# Approved: PR #81 ports patsy-lite to formulaic

## Summary

Approved. Every acceptance item is met. patsy-lite builds its matrices
with `formulaic.model_matrix`, and no module under de_toolkit/ imports
patsy. pyproject.toml swaps `patsy>=1.0` for `formulaic>=1.1`, the floor
the DETK-0024 study names. The DETK-0024 fixes are in: bools become
categorical, matrices are cast to float64, names are quoted with
backticks, and errors are wrapped, including a design with no left-hand
side. The only formula pins that change are the ones DETK-0040, DETK-0049
and DETK-0080 allow. The airway designs build byte-identical matrices
before and after the port. The R job is green: 1788 passed, and the airway example and the DESeq2/Firth tests ran.

## Artifacts

- PR #81 reviewed at 2a09e21

## Findings

- Checks: `uv run pytest` gives 1738 passed and 63 skipped; R is not
  installed here. `tests/patsy_lite` gives 75 passed. `ruff check` and
  `ruff format --check` are clean, and `uv lock --check` is ok. CI is green
  on 3.11, 3.12 and 3.13, ruff, docs (strict), runtime-deps-only, CodeQL,
  and **test with R (bioconda)** (1788 passed, 13 skipped; every DESeq2/Firth test in tests/de/test_de.py ran except the two that are always skipped as too slow, and test_airway_example passed).
- Dependencies: the only runtime change in pyproject.toml is patsy to
  formulaic>=1.1. uv.lock adds formulaic 1.2.2, interface-meta and wrapt.
  `uv tree --no-dev --invert --package patsy` shows patsy coming in only
  through statsmodels in the `test` extra (DETK-0024, DETK-0048).
- Pins: compared with main, only these fixtures change.
  - DETK-0049 (columns reordered, values the same per column):
    interaction_star, interaction_star_refs, quote_interaction_star.
  - DETK-0040: interaction_colon, plus three error pins that become
    matrix pins: interaction_colon_ref, boolean_ref_upper and
    boolean_ref_python.
  - DETK-0080 (Accepted): quote_interaction_colon, an error pin that
    becomes a matrix pin.
  - Added only: docs_disease_status_batch_ref and the error case
    boolean_ref_unknown.
  - No other fixture and no error-message regex changed. np.log stays
    pinned as an error (DETK-0028).
- Airway: DESeq2 and Firth give the same results because their inputs
  are the same. On airway-shaped column data (four cell lines, dex
  trt/untrt), I built `counts ~ cell + dex[untrt]` (the example's
  design), `dex[untrt] ~ cell + counts` and `dex[untrt] ~ counts` with
  main's patsy_lite and with this branch. The lhs and rhs of all three
  are `DataFrame.equals`-identical, with the same names, order and
  dtypes. The design has no interaction, so the DETK-0049 order change
  does not apply. In CI, the airway example ran end to end in the R job,
  and so did the DESeq2/Firth tests against their known values.
- Edge cases probed, with the right results:
  - missing values in a categorical or bool column drop the sample, as
    patsy did
  - `flag[TRUE]` gives `flag__False`
  - integer level lists and references give `batch__1`/`batch__3`
  - `-1`/`0` give a matrix with no intercept
  - `flag*g` and `g:flag` give their interaction columns
  - a level list that leaves out a level in the data now raises an error
    instead of formulaic's silent drop
- Docs: formulas.md names formulaic as the engine. It documents
  booleans, interactions and column order. Its disease_status
  (`batch[1]`) and continent (sorted) examples match the pins. The np.log
  sentence is left to release/formula-rename. The CHANGELOG has both
  entries the acceptance asks for: the interaction is now the last
  column under `--last-term-only`, and the error-text changes.
- Nit, non-blocking: the PR description still calls DETK-0080
  "Proposed". It was accepted (e3e79d8). Worth updating so the PR
  matches the record.
- Nit, non-blocking: `formulaic>=1.1` is appended at the end of
  `dependencies` instead of in alphabetical order.
- Nit, non-blocking: `except Exception` around `model_matrix` turns
  every failure, a bug included, into PatsyLiteParseError ("Misspecified
  column"). This is what the acceptance asks for ("every invalid
  formula"). The original is kept as `__cause__`.
- Pre-existing, not a regression: a reference or level written as a
  number is always passed as a number (`repr_val`). So `s[2]` on a
  column of the strings "1"/"2" fails. It failed the same way on patsy.

## Questions

None. No decision needed. Suggestion for Adam, optional: the airway
example's results are not pinned numerically. The R test only checks
that the pipeline runs. A formula pin for `counts ~ cell + dex[untrt]`
on airway-shaped data would make "same results on airway" a test
instead of a reviewer's check. It could go in release/formula-rename or
later.
