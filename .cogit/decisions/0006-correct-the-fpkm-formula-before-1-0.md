---
template: adr
state: Accepted
authority: [human]
date: 2026-11-09
from: {node: release/tpm-cpm, step: s1}
applies: [release/tpm-cpm]
revisions:
  - {date: 2026-11-09, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A: fix the FPKM formula before 1.0, as its own node"}
---

# Correct the FPKM formula before 1.0

## Background

`detk-norm fpkm` is meant to compute Fragments Per Kilobase per Million
reads: each count divided by the feature's length in kilobases and by the
sample's total counts in millions, `count * 1e9 / (length_bases *
library_size)`. The docs page (`docs/tools/norm.md`) describes exactly that.
The code (`FPKMCounts` in `de_toolkit/norm.py`) instead computes
`count / (1e6 * length_bases)`: it never divides by library size, and the
length factor is off by 10^9 relative to the documented unit. The test
`test_fpkm` asserts the current (wrong) values. Found while adding TPM under
#24, which reads the same lengths file.

## Context

- Until this node, `detk-norm fpkm` could not run from the CLI at all (the
  lengths file was read as a table), so the wrong numbers can only have
  reached users through the Python function `fpkm()` or 0.9.12 on PyPI,
  where the same code shipped.
- Under DETK-0001 (Proposed) output formats are promised from 1.0: after
  the tag a fix is a breaking change in the values `fpkm` writes.
- This is a scientific-correctness question and reaches beyond #24, so it is
  the human's, not the developer profile's.

## Options

### Option A: fix the formula in 1.0 (recommended)

Divide by length in kb and by library size in millions, update `test_fpkm`
to the documented values, note it under "Changed" in the CHANGELOG as a
correction of 0.9.x output. A separate small node or issue.

### Option B: keep the arithmetic, change the docs

Document what the code does. It is then not FPKM, so the name misleads.

### Option C: remove `fpkm` in 1.0 in favour of `tpm`

TPM is the unit most people want; dropping FPKM shrinks the promise, at the
cost of anyone who scripts `detk-norm fpkm`.

## Decision

Option A, chosen by Adam on 2026-11-09: fix the formula before 1.0 is
tagged, as its own node (`release/fpkm`), so #24 stays about CPM and TPM.

## Consequences

With A, `fpkm` output values change (by the library size and a constant
factor) relative to 0.9.12, and the CHANGELOG must say so. With B or C the
docs page changes instead. Nothing in #24 depends on the answer: `tpm`
computes its own per-kilobase rate.
