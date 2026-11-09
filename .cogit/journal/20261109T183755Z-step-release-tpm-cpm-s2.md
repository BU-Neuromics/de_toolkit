---
kind: step
time: 2026-11-09T18:37:55Z
by: DETK/reviewer
node: release/tpm-cpm
step: s2
branch: node/24-tpm-cpm
verdict: changes
commits: []
decisions: []
---


# Review of PR #40: detk-norm cpm and tpm

## Summary

The statistics are right. By hand on the tests' 3x2 example (a = 1,3,0;
b = 2,4,4; lengths g1 1000, g2 2000, g3 4000), CPM gives a = 250000,
750000, 0 and b = 200000, 400000, 400000. The per-kb rates are a = 1, 1.5, 0
(sum 2.5) and b = 2, 2, 1 (sum 5), so TPM gives a = 400000, 600000, 0 and
b = 400000, 400000, 200000. The tests assert these values and the CLI writes
them. Lengths are matched to rows by name, the output keeps the counts row
order, and missing, zero, negative and non-numeric lengths are refused with
a clear error. The `library` and `fpkm` CLI fixes work. The report views
(library-size bars for cpm, length quantiles for tpm) build, and the module
JSON is valid. The docs, CHANGELOG and DETK-0005 match the code. FPKM
arithmetic is unchanged, as DETK-0006 requires (it moves to release/fpkm).

The new `read_lengths` needs changes before this merges. A lengths file
with numeric feature IDs is refused, and a duplicated ID silently changes
the output. `tpm` adds both of these to the 1.0 surface, and `fpkm` shares
them.

## Artifacts

- PR BU-Neuromics/de_toolkit#40, branch node/24-tpm-cpm at e8d49ed
- Local checks: `uv run pytest` 167 passed, 49 skipped (no R), 1 warning
  (rdflib ConjunctiveGraph deprecation); `ruff check` clean; `ruff format
  --check` clean (112 files); `mkdocs build --strict` clean
- CLI smoke runs: `detk-norm cpm`, `tpm`, `library`, `fpkm` on a small
  file; edge cases with numeric IDs, duplicate IDs, a non-numeric length and
  an all-zero sample; `tpm` with `--report-dir` (JSON + HTML report written)
- `gh pr checks 40` at e8d49ed: ruff, the four Python test jobs, CodeQL
  and Analyze all pass. "test with R (bioconda)" was still pending. On
  871c58a, whose code is identical to e8d49ed outside `.cogit/`, the R job,
  the docs build and the tests passed. That run reports "failure" overall,
  but every job it lists passed or was skipped.

## Findings

1. de_toolkit/norm.py:368 (`read_lengths`, `dtype=str`) with
   de_toolkit/common.py:306 (counts read with an inferred index dtype).
   When feature IDs are numeric, such as Entrez gene IDs, the counts index is
   int64 but the lengths index is str. Every feature is then reported "not
   found in the lengths parameters" and `detk-norm tpm` (and `fpkm`) exits 1.
   I reproduced this with IDs 101/102/103 in both files. Numeric IDs are
   common, and the error message points the user at the wrong cause.
   Suggested fix: match on strings on both sides (`count_df.index.astype(str)`
   in `_lengths_for`, keeping the original index on the output), and add a
   test with numeric IDs. Severity: major.

2. de_toolkit/norm.py:350 (`_lengths_for`, `lengths[count_df.index]`). A
   lengths file that lists the same ID twice makes `.loc`-style indexing
   return both entries. The TPM output then has an extra row. In my run g1
   appeared twice and the column of 4 rows summed to 1e6, so every value was
   wrong, with no error or warning. This contradicts the docs
   (docs/tools/norm.md:103: "the same rows, in the same order, as the counts
   file"). Suggested fix: reject duplicated IDs in `read_lengths`/`_lengths_for`
   with a NormalizationException, or warn and keep the first, and test it.
   Severity: major.

3. de_toolkit/norm.py:373-374 (header detection). Any first line whose second
   field is not numeric is dropped as a header. A headerless file whose first
   length is bad (`NA`, `abc`) loses that feature. It is then reported as
   "not found", not as "not a positive number", which is confusing but not
   silent. Severity: minor.

4. tests/norm/test_norm.py: the all-zero sample path (NaN output plus a
   warning, norm.py:395 and :438) is documented in the docs and DETK-0005 but
   not tested. I confirmed by hand that the CLI writes empty (NaN) cells for
   that column. Severity: minor.

5. Out-of-scope files (`git diff --stat origin/main...HEAD`):
   de_toolkit/crate.py adds `cpmcounts`/`tpmcounts` to SUBTOOLS. This is
   needed for RO-Crate provenance of the new modules, the s1 result discloses
   it, and it is justified. The `.cogit/` changes (DETK-0005/0006, journal,
   the new release/fpkm node, cut.md `prev`) are cogit bookkeeping for this
   node and DETK-0006. All other files are in scope. Severity: none.

## Questions

- DETK-0005 is Provisional under the developer's own authority, yet by its
  own Consequences it adds `cpm`/`tpm` to the 1.0 stable surface (DETK-0001).
  The developer profile says such a decision "is a question for the human".
  Should Adam confirm DETK-0005 at s3, or should it have been Proposed? The
  shape it chose, the CLI the issue suggests, looks right to me.
- CHANGELOG: should the `tpm` entry say that lengths must be positive and
  that a header line is accepted? These are new behaviours of the shared
  lengths reader, which `fpkm` now also uses.
