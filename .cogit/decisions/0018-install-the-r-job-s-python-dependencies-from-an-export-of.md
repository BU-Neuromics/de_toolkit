---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/ci-lock, step: s1}
applies: [release/ci-lock]
allowed_by: [reasonable]
reason: "the R job tested PyPI's latest pandas/matplotlib, not the locked set users get"
---

# Install the R job's Python dependencies from an export of uv.lock

## Background

detk's CI has two kinds of test job. The `test` matrix (Python 3.10 to
3.13) installs with `uv sync --locked --dev`, so it runs on exactly the
versions `uv.lock` pins. It has no R, so the R-backed tests (DESeq2,
fgsea, logistf) skip there. The `test-r` job gets R and the Bioconductor
packages from bioconda through micromamba, and until now installed detk
with `pip install -e '.[test]'` into micromamba's Python 3.12. That
resolved against PyPI on the day of the run: in the review of #54 it
tested pandas 3.1.1 and matplotlib 3.11.2 where the lock has 3.0.5 and
3.11.1. The only job that exercises the R integration was testing a
different environment from the one users and the other jobs get.

## Context

- The R job must keep R and Bioconductor from bioconda (compiling DESeq2
  and fgsea from source is slow and fragile), so its Python is the
  micromamba environment's interpreter, not one uv provisions.
- The Python packages it tests must be the ones `uv.lock` pins, and a
  stale lock must fail the job rather than be silently re-resolved.
- The method should be short, readable and robust against the conda
  packages already in the environment.
- The job cannot be run locally (no R, no micromamba here); the PR's CI
  run is the test.

## Options

1. **`uv export --frozen` to a requirements file, `pip install -r` it into
   the environment's Python, then `pip install --no-deps -e .`.** The
   export carries environment markers, so pip picks the pins for the
   environment's Python version. `--frozen` uses the lock as written.
   pip adds packages without removing anything conda put there. Two
   tools, but each does one plain thing; easy to read in the log.
2. **`uv sync --locked` with `UV_PROJECT_ENVIRONMENT=$CONDA_PREFIX`.**
   One command and `--locked` checks the lock is current, but `uv sync`
   is exact by default: it would uninstall Python packages in the conda
   environment that the lock does not list (conda's own pip, setuptools,
   anything bioconda pulled in). `--inexact` avoids that, at the cost of
   pointing uv at a prefix it does not own; more surprising when it
   breaks.
3. **`uv pip sync` / `uv pip install -r` the export with `--python`
   pointing at the environment's interpreter.** Same effect as option 1
   with uv's installer; `uv pip sync` has option 2's removal problem,
   and `uv pip install` into a conda prefix needs `--system`-style
   flags. No gain over pip for one job.
4. **Keep `pip install -e '.[test]'` and add a constraints file.** Still
   needs the export; no simpler than option 1.

## Decision

Option 1. The job installs uv with `astral-sh/setup-uv` (the version the
other jobs pin), runs `uv export --frozen --group dev --no-hashes
--no-emit-project` into `$RUNNER_TEMP`, pip installs that list into the
micromamba Python, installs detk itself with `--no-deps -e .`, runs
`pip check`, and prints the Python, numpy, pandas and matplotlib
versions. It exports the `dev` group, not only the `test` extra, so the
R job installs the same set the `test` matrix syncs (jsonschema,
roc-validator, vl-convert-python as well as pytest and pytest-cov) and
runs a superset of its tests instead of skipping those. Option 1 is the
one that cannot disturb the conda environment and whose log shows
plainly what was installed.

## Consequences

- The R job now tests the locked pandas, numpy and matplotlib; bumping
  them is a lock change that both kinds of job see at once.
- `--frozen` does not check that `uv.lock` is current with
  `pyproject.toml`; the `test` matrix's `uv sync --locked` does, so a
  stale lock still fails CI.
- The R job's Python (3.12) must satisfy `requires-python` and have
  wheels for every pin; if a pin has no wheel for it, the job fails
  loudly at install rather than testing something else.
- Revisit if uv gains a clean way to install into a foreign prefix
  without removing packages, or if the R job moves off micromamba.
