---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/ci-lock, step: s1}
applies: [release/ci-lock]
allowed_by: [reasonable]
reason: the lock resolves for 3.14 but CI and classifiers stop at 3.13; 1.0 should promise only what CI tests
revisions:
  - {date: 2026-11-09, by: DETK/developer, change: the Python floor is 3.11 now that DETK-0016 is merged, why: review of s2}
---

# Python 3.14 is best effort for 1.0

## Background

detk 1.0 declares `requires-python = ">=3.11"` (DETK-0016 dropped 3.10)
and lists classifiers for Python 3.11 to 3.13; the CI test
matrix runs exactly those versions. Python 3.14 was released in October
2025. `uv.lock` already resolves for 3.14 (it has no upper bound), so
`pip install detk` on 3.14 will try to install it. The question is
whether 1.0 promises that this works.

## Context

- A classifier or a CI matrix entry is a promise users read: "this
  version is supported and tested".
- detk depends on numpy, pandas, scipy, statsmodels, matplotlib and,
  through wrapr, R; each has to ship 3.14 wheels and behave the same
  before detk can claim 3.14.
- 1.0 is about a stable interface (DETK-0001), not about chasing the
  newest interpreter; widening the matrix now adds a CI job and a
  possible source of release-blocking failures for no 1.0 feature.
- `requires-python` has no upper bound, so nothing stops a user trying
  3.14; the choice is only what is promised.

## Options

1. **Best effort: do not add a 3.14 classifier or CI matrix entry; say
   in the changelog that 3.14 is expected to work but is not tested or
   promised for 1.0.** No new CI cost; the promise stays equal to what
   CI tests; users on 3.14 can still install and report problems.
2. **Support 3.14 in 1.0: add the classifier and a matrix entry.** A
   stronger promise, and the lock suggests it might pass, but it ties
   the 1.0 release to every dependency's 3.14 behaviour and adds a job
   whose failures would block the release.
3. **Exclude 3.14: cap `requires-python` at `<3.14`.** Honest about
   testing but blocks users for no known failure, and upper caps on
   `requires-python` cause resolver trouble downstream.

## Decision

Option 1. The 1.0 promise covers the Python versions CI tests (those the
classifiers list, 3.11 to 3.13);
3.14 is best effort. No 3.14 classifier, no 3.14 CI entry, no upper cap,
and the README keeps saying what `requires-python` says. The changelog
states the stance so users know.

## Consequences

- Users on 3.14 can install detk and are welcome to report problems; a
  3.14-only failure is a bug to fix when practical, not a 1.0
  regression.
- Promoting 3.14 to supported later is one matrix entry and one
  classifier, in a minor release, once it passes.
- Revisit when 3.14 is the version most users get by default, or when a
  dependency drops a version detk tests.
