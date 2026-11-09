---
kind: task
objective: CI's R job installs detk from uv.lock, so the R tests run on the versions users get; Python 3.14 is recorded as best effort, not a 1.0 promise
acceptance:
  - the R job installs the locked dependencies (uv sync --locked or an export of uv.lock) into its R-enabled environment and the suite passes there
  - a Provisional record says Python 3.14 is best effort for 1.0, and the docs or classifiers do not promise it
scope: [.github/workflows/ci.yml, pyproject.toml, README.md, +CHANGELOG]
issue: 58
visited: fc05692
---

# Run the R tests on the locked environment

## Implementation plan

- [ ] @developer Make the R job install from uv.lock; record the method and Python 3.14 as best effort (Provisional); open the PR <!-- s1 -->
- [ ] @reviewer Review the PR and the R job's run <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the review of de_toolkit#54: the
R job ran `pip install -e '.[test]'` into micromamba's Python, which
pulled pandas 3.1.1 and matplotlib 3.11.2 where the lock has 3.0.5 and
3.11.1. The lock already resolves for 3.14; the classifiers and CI stop
at 3.13.
