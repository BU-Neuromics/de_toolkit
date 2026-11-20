---
kind: task
objective: 'Tutorial pages in the docs site run as tests: each page''s shell blocks run in order in CI and its shown outputs are checked, so the tutorials are the docs and integration tests at once (DETK-0064)'
acceptance:
  - 'a pytest collector in new:tests/tutorials/ runs every docs/tutorials/*.md page (and any page carrying the tutorial marker, such as docs/recipes/) as one test: each bash block in order under bash -euo pipefail in a fresh working directory per page, with the installed detk on PATH'
  - 'the markers of DETK-0064 Option A work and are tested on small fixture pages: requires (skips with the reason when R, an R package or mlr is missing), expect (compares the previous block''s output, exactly or by a pattern), fails (the block must exit non-zero), hidden; a failing block reports the page, the block''s line and its stderr'
  - 'an optional new:tests/tutorials/test_<page>.py receives the page''s working directory after the page has run, for deeper checks'
  - 'docs/tutorials/index.md lists the tutorials, with what each needs (R, Miller) and how to run one locally; the Tutorials section is in the nav; mkdocs build --strict passes and the markers do not show on the site'
  - 'CI runs the tutorials that need no R in the test jobs and all of them in the R job; docs/dev/ says how to write a tutorial page and its checks'
from: [DETK-0064]
scope: [new:docs/tutorials/, new:tests/tutorials/, docs/dev/, +mkdocs.yml, +.github/workflows/ci.yml, +pyproject.toml, +CHANGELOG]
prev: [DETK-0064, release/statsmodels-test]
---

# Run tutorials as tests

## Implementation plan

- [ ] @developer Build the collector and its markers with fixture pages and tests, the tutorials index and nav, the CI wiring and the docs/dev how-to; open the PR <!-- s1 -->
- [ ] @reviewer Review the collector (ordering, working directory, skips, failure messages) and the CI wiring; build the docs <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 on Adam's request for "fully functional and documented
tutorial workflows that both serve as user facing docs and as integration
tests", with the format of DETK-0064 (executable Markdown run by pytest;
Quarto weighed and not chosen). After release/statsmodels-test, which also
edits the CI workflow. New pages go under `docs/tutorials/`.
