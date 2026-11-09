---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/tpm-cpm, step: s1}
applies: [release/tpm-cpm]
allowed_by: [reasonable]
reason: "a subcommand per unit matches deseq2/library/fpkm and keeps library's output unchanged under the 1.0 CLI promise"
revisions:
  - {date: 2026-11-09, by: DETK/developer, change: "Record the lengths-file rules tpm adds to the 1.0 surface: IDs matched as text, duplicate IDs refused, header only when the length field is non-numeric and not a missing-value token", why: review of s2}
---

# CPM and TPM as dedicated detk-norm subcommands

## Background

`detk-norm` normalizes count matrices through one subcommand per method
(`deseq2`, `library`, `fpkm`), each emitting a report module of the `norm`
family. Issue #24 adds counts per million (CPM) and transcripts per million
(TPM) and leaves open whether CPM is a new subcommand or a `--scale` option
on `library`. Under DETK-0001 (Proposed) the subcommand names, arguments and
output formats are the 1.0 stable surface, so the shape chosen here is
promised from 1.0 on.

## Context

- `library` already computes the CPM divisor (column sums) and outputs
  proportions; existing pipelines may rely on that output.
- TPM needs the same two-column lengths file `fpkm` consumes.
- Report views and RO-Crate provenance key on the module name, the
  lowercased class name (`SUBTOOLS` in `crate.py`, the registry in
  `report_specs.py`).
- Criteria: discoverability in `detk-norm --help`, no change to existing
  outputs, consistency with the existing subcommands, cost of the promise.

## Options

### Option A: `cpm` and `tpm` subcommands (chosen)

`detk-norm cpm <counts_fn>` and `detk-norm tpm <counts_fn> <lengths_fn>`,
classes `CPMCounts`/`TPMCounts` (modules `cpmcounts`/`tpmcounts`). Output is
the input matrix shape and row order, values in units per million, so every
column sums to 1e6 (NaN for an all-zero sample, with a warning). Lengths are
in bases, as for `fpkm`, and must be positive. The lengths file, shared
with `fpkm`, matches feature IDs as text (so numeric IDs work), refuses a
feature listed twice, and may start with a header line, recognized only
when its length field is text other than a missing-value token such as
`NA`. Discoverable, consistent,
leaves `library` untouched; two more names to keep stable.

### Option B: `library --scale=N`, plus a `tpm` subcommand

One fewer subcommand, but CPM is then spelled `library --scale=1e6`, which
nobody searches for, and an option on `library` is as much a promise as a
subcommand.

### Option C: a single `--units` option across subcommands

Over-general for two units and would reshape the existing commands.

## Decision

Option A, the CLI the issue suggests. A subcommand per unit is how the tool
is already organized and keeps `library`'s output exactly as it was. The
report views reuse the existing builders (library-size bars for `cpm`,
feature-length quantiles for `tpm`).

## Consequences

- `cpm`, `tpm`, their arguments and the per-million output are part of the
  1.0 surface once DETK-0001 is accepted.
- `library` remains, producing proportions; the docs point from it to `cpm`.
- Revisit if a `--scale` on `library` is wanted for other factors, which
  could be added later without breaking `cpm`.
