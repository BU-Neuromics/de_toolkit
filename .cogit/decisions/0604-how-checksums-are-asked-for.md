---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-1}
applies: [release-1-1/crate-checksums]
issue: 175
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's decision via the driver session, 2026-11-27 (\"Yes, accept all recommendations\"): Option A, checksums on request with DETK_CHECKSUMS=1"}
---

# How checksums are asked for

- Proposed by: the plan session, 2026-11-27, for the driver to confirm

## Background

1.1 records SHA-256 checksums of each native step's input and output files
"optionally" (Adam's direction). How a user asks for them is open.
Hashing large count matrices costs time on every step.

## Context

- Hashing is optional, so the default output stays as in 1.0.
- A checksum is only useful if every step of an analysis has one.

## Options

**A. An environment variable, `DETK_CHECKSUMS=1`** (recommended). Set once
for a whole analysis, read by every command's report writer; no option is
added to any command's help. Documented in docs/report.md.

**B. A common option `--checksums`** on every command. Visible in help,
but must be passed to every step, and a step without it leaves a gap.

**C. At report time, `detk-report --checksums`**, hashing the files the
module JSON names when the report is built. One place, but it hashes the
files as they are then, not as the step read or wrote them.

## Decision

Recommended: **A**, for the driver to confirm. C could be added later as
a check that files are unchanged since their step.

## Consequences

`release-1-1/crate-checksums` waits on this record.
