---
template: adr
state: Proposed
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1}
applies: [release-1-0-1/count-checks, release-1-0-1/count-checks-readers]
issue: 172
---

# The exit status of a malformed counts file

- Proposed by: the plan session, 2026-11-27, for the driver to confirm

## Background

Adam's direction for 1.0.1 (via the driver session, 2026-11-27) is that the
count checks (duplicate sample headers, duplicate feature IDs, negative
counts, zero-depth samples) "exit 2 naming the offender". DETK-0031,
Accepted and documented in docs/concepts.md and every command's help, gives
exit 2 to a usage error only, a wrong command line, and exit 1 to "any other
failure: a bad input file, a missing R or R package, a step that fails".
A malformed counts file is a bad input file. The two disagree, and the
codes are part of the 1.0 promise.

## Context

- An agent uses the code to decide what to fix: 2, its command line; 1,
  the data or the environment (docs/concepts.md says so in those words).
- Every existing data error (a ragged sample sheet, DETK-0450; no shared
  samples; the size-factor failure) exits 1.
- The direction's point is that these fail loudly and name the offender;
  "2" may have been shorthand for a non-zero exit rather than a choice
  against DETK-0031.

## Options

**A. Exit 1, as DETK-0031 says** (recommended). One stderr line
`<command>: error: <cause>` naming the header, feature, sample or value.
Consistent with every other data error and with the documented table.

**B. Exit 2, as the direction says.** Reclassifies one kind of bad input as
a usage error: changes the meaning of a documented code in a patch, and an
agent told by the docs that 2 means "fix your command line" would look in
the wrong place.

**C. A new code for invalid input.** DETK-0031's Option B, which Adam did
not take; adds a code in a patch.

## Decision

Recommended: **A**, pending the driver's confirmation of Adam's intent.
If Adam meant 2 deliberately, B needs its own reasoning against the
promise, as DETK-0600 gives for fgsea.

## Consequences

- `release-1-0-1/count-checks` and `count-checks-readers` wait on this
  record; their acceptance says "the status DETK-0601 settles".
- Under A, nothing in docs/concepts.md's exit-code table changes.
