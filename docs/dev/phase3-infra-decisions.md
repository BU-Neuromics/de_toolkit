# Phase 3: infrastructure decisions

Date: 2026-08-11. Companion to `phase2-report-viz-research.md`. Three
infrastructure decisions made together because they interact: the docs system,
the Python packaging/tooling stack, and the fate of Snakemake.

## 1. Documentation: MkDocs Material on GitHub Pages

**Decision: migrate from Sphinx/ReadTheDocs to MkDocs with the Material theme,
built and deployed to GitHub Pages by GitHub Actions.**

Context: the ReadTheDocs build has been broken since `setup.py` was deleted —
`readthedocs.yml` is a legacy v1 config (`python: 3.6`, `setup_py_install`)
that RTD no longer supports, and the live site is a stale cached build from the
2021 era. Rather than repair a config for a hosting service we no longer need,
we move to the system with the greatest current acceptance in the Python
ecosystem.

Why MkDocs Material:

- It is what the tools this project now builds on use themselves: uv, ruff,
  FastAPI, Pydantic, Polars, Typer. It is the de facto default for new Python
  project docs in 2026.
- Markdown-native. The existing RST corpus is small (~12 short pages) and much
  of it is stale enough that migration is mostly *rewriting*, not converting —
  the conversion cost argument for staying on Sphinx does not apply here.
- Single YAML config, built-in client-side search, dark mode, mobile layout —
  no theme shopping, no `conf.py`.
- `mkdocstrings[python]` renders API reference from the existing docstrings,
  replacing `sphinx.ext.autodoc`.
- Hosting on GitHub Pages keeps docs deployment inside the repo's existing
  CI/CD surface (one workflow, `mkdocs gh-deploy`) instead of a second
  service with its own config format and build environment.

Considered and rejected:

- **Sphinx + furo, still on RTD**: keeps RST and gets a modern theme, but
  keeps two config systems (conf.py + .readthedocs.yaml), a second hosting
  service, and a markup language none of the surrounding ecosystem uses.
- **Docusaurus / Starlight**: strong systems, but a Node toolchain in a pure
  Python repo fails the "simpler" requirement.
- **mdBook / Zola / raw Pages**: no Python API-reference story.

## 2. Packaging & tooling: uv + hatchling + ruff

**Decision: adopt uv as the package/project manager, hatchling as the build
backend, and ruff as linter+formatter. Not Poetry.**

Why uv over Poetry:

- uv is the tool the ecosystem has converged on since 2024; it is faster by
  orders of magnitude, and it consumes standard `[project]` (PEP 621) metadata
  and `[dependency-groups]` (PEP 735) directly. Our `pyproject.toml` is
  already PEP 621 from Phase 1 — adopting uv changes almost nothing;
  Poetry would be a heavier tool for the same job.
- One binary covers lock (`uv.lock`, committed), sync, run, build, and Python
  version management. Contributors without uv can still `pip install -e .`,
  because the metadata stays standard — uv is additive, not captive.

Build backend: **hatchling** replaces setuptools. It is the most widely
adopted modern backend, has first-class package-data handling (the vendored
Vega bundles and `report.html` must ship in the wheel — asserted in
`tests/report/test_report_render.py`), and drops the `MANIFEST.in` +
`include-package-data` legacy. `uv_build` was considered (same author, fine
backend) but hatchling's broader adoption makes it the conservative choice for
a package other people will build from sdist.

Lint/format: **ruff** (check + format), replacing nothing — the project has
never had a linter — which is exactly why it needs one. Rule selection starts
conservative (pycodestyle/pyflakes defaults + pyupgrade + bugbear) with
autofixable rules applied in the Phase 3 modernization sweep and the rest
ratcheted later.

CI moves to `astral-sh/setup-uv` + `uv sync --locked` + `uv run pytest`, which
also gives dependency caching keyed on the lockfile for free. The R job keeps
micromamba for the R side and uses uv for the Python side.

## 3. Snakemake: removed from the repo's own machinery

**Decision: drop Snakemake as an internal dependency. detk remains pure
Python. Workflow managers are documented as *integration targets*, not used as
internal machinery.**

Investigation result: Snakemake was never a runtime dependency of the package.
Its entire footprint was:

1. `tests/report/Snakefile` — a 4-rule pipeline (gunzip → detk-stats →
   detk-filter → detk-report generate) driven by `subprocess.run("snakemake
   --forceall")` in the report e2e test. This test has been failing since
   modern Snakemake began requiring `--cores` (issue #12), and silently
   skipping wherever Snakemake isn't installed — including, today, both CI
   jobs.
2. Doc examples in `quickstart.rst` / `workflow/intro.rst` showing detk inside
   a Snakemake workflow.
3. A pin in the stale, pre-pyproject `Pipfile` (deleted this phase).

On the executor-engine question (the suspected original motivation — using
Snakemake's executors to submit to clusters/cloud): that capability matters to
*users' pipelines that call detk*, not to detk itself. detk's tools are
single-invocation CLI filters — exactly the shape every workflow manager
(Snakemake, Nextflow, WDL/Cromwell, plain Make) is designed to orchestrate.
Baking one manager into the package would narrow, not widen, deployability.
The right seam is: detk provides well-behaved CLIs + the JSON report layer;
any executor engine orchestrates them. So the use case is real but is served
by staying out of the way, and no alternative dependency is needed to replace
Snakemake — the replacement is nothing.

Consequences:

- The report e2e test is rewritten as a plain pytest that chains the same detk
  CLI invocations via `subprocess` — it now actually runs everywhere, in every
  CI job, with no extra dependency. Closes #12 by deletion.
- Docs keep (updated) Snakemake and Nextflow snippets as integration examples
  — showing users how to embed detk in the manager they already use.
- The worked-example issue (#16) should ship its pipeline as a plain shell or
  Python script by default, with the Snakemake variant as an optional
  illustration, not a requirement.
