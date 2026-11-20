---
kind: step
time: 2026-11-20T14:52:35Z
by: DETK/reviewer
node: release/size-factors
step: s2
branch: review/size-factors
verdict: changes
commits: []
decisions: [DETK-0082]
---

# Changes asked: Review the PR

## Summary

Changes asked: decide a header line for the size-factors file (DETK-0082 Proposed, recommends sample<TAB>size_factor) and state the header choice in --help/commands.md; otherwise correct, tests thorough, CI green incl. R job

## Artifacts

## Findings

Review of PR #88 at fd6a1b1 (diff against origin/main 92d4fab).

Checked
- norm.py: `write_size_factors` writes `self.size_factors` (built with `.tolist()`, so plain Python floats; `repr` round-trips exactly), in the counts file's column order, names untouched; written only for `deseq2` with the option; an unwritable path logs and exits 1. Correct.
- Tests: tests/norm checks zero-padded unsorted names, file == module == JSON `properties.size_factors`, counts output and JSON unchanged with/without the option, nothing extra written without it, unwritable path exits 1; the R-gated test compares the file with `DESeq2::estimateSizeFactors`. tests/cli pin now "writes the file". Locally (no R): tests/norm + tests/cli 1555 passed, 21 skipped. CI all green, including `test with R (bioconda)` (2038 passed, 22 skipped; tests/norm ran with no skips, so the R comparison ran and passed).
- docs/example.md, run.sh, CHANGELOG (under Fixed) describe the written file; commands.md usage unchanged. Acceptance met as written.

Changes asked
1. Header line (DETK-0082, Proposed, recommendation: Option A). The file has no header. Default readers (`pandas.read_csv(f, sep="\t")`, R `read.delim(f)`) take the first line as a header and silently drop the first sample; a headerless file also does not describe itself to an agent. For a 1.0 output format I recommend a `sample<TAB>size_factor` first line. Neither the help, DETK-0029 nor the acceptance settles it, so it is recorded as DETK-0082 for the driver/Adam rather than decided here. If accepted: write the header, have the tests read it (`_read_size_factors`, the cli pin), and update CHANGELOG.
2. Whichever way DETK-0082 goes, say it in the `--help` text (and copy it into skills/detk/references/commands.md): "...tab separated file with a header line `sample`, `size_factor`" or "...with no header line". Today only the CHANGELOG says so, and agents read the help.

If DETK-0082 is rejected (no header), item 2 alone remains and the PR is otherwise approvable.

Not blocking
- An unwritable --size-factors path exits 1 after the normalized counts are already written (to -o or stdout). Acceptable; noted only.
- Out of scope, for a follow-up: skills/detk/references/airway.md:73 drops `--size-factors` (removed when it wrote nothing; "the size factors go into the report"); now it works it could be restored to match run.sh. docs/tools/norm.md shows the old docopt help text.

## Questions

- DETK-0082 detk-norm deseq2 --size-factors file: a header line or none (#93)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
