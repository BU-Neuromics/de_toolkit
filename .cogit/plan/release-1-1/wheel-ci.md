---
kind: task
objective: after release.yml publishes, a job installs that version from PyPI in a clean environment with R and runs counts through to a validated crate with lineage assertions
acceptance:
  - the job installs de_toolkit==<tag> from PyPI (no checkout on the import path), runs detk-filter -> detk-norm deseq2 -> detk-de deseq2 -> detk-enrich fgsea -c -> detk-report on packaged test data, validates the crate with the Process Run Crate validator, and asserts the lineage edges of release-1-0-1/lineage-test; a failure fails the release workflow run
  - the job is shown to fail on a broken crate (a test or a dry run against a deliberately edited crate), and it runs in the 1.1 cut
scope: [.github/workflows/release.yml, tests/release/, +docs/dev/]
---

# Release CI tests the published wheel from counts to a validated crate

## Implementation plan

## Notes
