---
kind: step
time: 2026-11-09T19:55:57Z
by: DETK/reviewer
node: release/gather
step: s2
branch: node/25-gather
verdict: approve
commits: []
decisions: []
---


# Re-review of #52: detk-util gather (after a6ec964)

## Summary

I reviewed `node/25-gather` at a6ec964 independently and checked each
finding from the earlier s2 review. The blocking finding and the two low
findings are fixed, the info finding on glob order is addressed, and the
fixes broke nothing I could find. I approve.

- **Earlier 1 (medium), multi-column htseq: fixed.** An htseq file with
  more than one count column now exits with code 1. The message gives the
  number of count columns, says that htseq-count writes no header, and
  suggests `--column=N` or one run per sample. This also happens when the
  file is gathered beside a single-column file. `--column=2` gathers the
  second BAM's column, and an out-of-range `--column` is an error.
  DETK-0012's "Default column" text and Consequences, util.md, the CLI help
  and the docstring all say this. A test covers it.
- **Earlier 2 (low), number check: fixed.** All of these are refused:
  `nan`, `NaN`, `inf`, `-inf`, `Infinity`, `1_000`, `1,000`, `" 5"`,
  `"5 "`, `0x10`, `.`, `e5`, `1e` and full-width `１`. All of these are
  accepted and written exactly as given: `1e5`, `1E-3`, `1.5e+06`, `007`,
  `0.000`, `-0`, `+5`, `5.` and `.5`. Leading zeros in values survive.
- **Earlier 3 (low), naming rationale: fixed.** The behaviour is unchanged,
  and DETK-0012, the docs and the help now describe it correctly. A lone
  `s1/quant.sf` gives `quant`, two salmon directories give `s1,s2`, and two
  `counts.txt` in different directories give `x,y`. `--name-from` works, and
  both a pattern that does not match and colliding names are errors. The
  same file given twice is refused.
- **Earlier 4 (crate input File entities):** out of scope (#45). I did not
  re-raise it.
- **Earlier 5 (info), glob order: done.** A quoted `'s*.txt'` gives
  `s1,s2,s3,s10,s11,s20`. A shell glob keeps the shell's order, as the new
  "Order" paragraph says.
- **Earlier 6 and 7 (info):** unchanged and still harmless.

Other behaviour I checked again:

- All four formats are detected. Mixed formats, unknown files and empty
  files are refused with clear messages, and so are bad values of
  `--format` and `--on-mismatch`.
- `--on-mismatch`: `error` gives a clear message, and `fill` and `drop`
  give the documented rows with a warning.
- Feature IDs are written exactly as given: `0001`, `1e5`, `NA`, `" 7"`,
  `ENSG1.2`.
- The `htseq_counters` and `params.files` in the report are right.
- A gathered htseq matrix feeds `detk-filter`, `detk-norm deseq2`,
  `detk-norm library` and `detk-stats rowzero` without changes.

The PR cannot be merged as it stands (finding 1), but the cause is a
CHANGELOG conflict with main, not the code. Merge main and get green CI
before s3.

## Artifacts

- Hands-on fixtures and outputs are in scratchpad `rr52/`: `num/`, `nat/`,
  `ids/`, `ds/`, `sup/`, the trial merge in `merged/`, and `checks.txt`.
  The earlier reviewer's fixtures in `rv52/` were reused.
- `uv sync`: ok
- `uv run pytest`: 247 passed, 49 skipped
- `uv run ruff check .`: all checks passed
- `uv run ruff format --check .`: 139 files already formatted
- `uv run --group docs mkdocs build --strict`: built. The only notice is
  the Material team banner.
- `gh pr checks 52`: CodeQL (actions, python) passed. The CI workflow
  (ruff, docs, tests 3.10 to 3.13, R) has **not run on a6ec964**, because
  the PR is `CONFLICTING`.
- Trial merge with `origin/main` (b94644c), taking main's CHANGELOG: the
  full suite gives 266 passed, 49 skipped. That includes main's new
  `tests/skills`, which passes with gather's new `detk-util` usage line.

## Findings

1. **medium (must be done before merge, not a code defect)** `CHANGELOG`
   and PR state. #52 is `CONFLICTING` with `origin/main`. Main has gained
   CHANGELOG entries since the branch point (#42, #49), and `git merge-tree`
   reports a content conflict only in `CHANGELOG`. Because of the conflict,
   GitHub has not run the CI workflow on a6ec964, so no CI tests or docs
   build cover the fix commit. Merge `origin/main`, keep both CHANGELOG
   entries, and wait for green CI before s3. My trial merge passed the full
   suite.
2. **low (outside scope; follow-up)** `docs/quickstart.md:7` shows
   `docs/simple_pipeline.png` (source `docs/simple_pipeline.svg:233,244`).
   The figure still has a "csvgather / bitbucket.org/adamlabadorf/csvgather"
   box as the first step. The quickstart text now uses `detk-util gather`,
   but the figure at the top contradicts it. The node's objective is
   "replacing csvgather in the documented workflow". Redraw the box as
   `detk-util gather` here or in a follow-up. The files are not in the
   node's scope.
3. **low (outside scope; for the orchestrator)** `skills/detk/` (on main
   since #42) does not mention `detk-util gather`. The note in
   `.cogit/plan/release/agent-skills.md` says the new commands of #24, #29
   and #25 "belong in them once merged", and DETK-0010 says new commands are
   added to the skill by hand. Under this node's scope that is not this
   PR's job, but no node appears to own it.
4. **info** `de_toolkit/util.py:609`. With a positional column, the
   non-numeric error shows a numpy repr: `column np.int64(0) holds
   non-numeric values` (seen with `--column=0` on an htseq file). This is
   cosmetic. `str(name)` would read better.
5. **info** `de_toolkit/util.py:435` (`_NUMBER`). The check is a syntax
   check, so `1e400` passes as "finite" and reads back as `inf` downstream.
   No quantifier writes such a value, so no change is needed.
6. **info** `de_toolkit/util.py:584-599`. With featureCounts and
   `--column` set to an annotation column (`--column=Length`), the sample is
   named after the column (`Length`). This is what the user asked for and
   is harmless.

## Questions

1. Who adds `detk-util gather` (and tpm/cpm and annotate) to
   `skills/detk/`? Is it a follow-up node, or part of the cut (finding 3)?
2. Should the quickstart figure be fixed in this PR, which would mean
   widening the scope to `docs/simple_pipeline.*`, or as a follow-up
   (finding 2)?
