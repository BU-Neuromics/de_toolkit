---
kind: step
time: 2026-11-23T14:59:59Z
by: DETK/reviewer
node: release/crate-stdout
step: s2
branch: review/crate-stdout
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: run a detk command to stdout and one to a file, read both crates, and check them with rocrate-validator

## Summary

Approved: stdout marker leaves no File, out.csv and a file named stdout (./stdout) are listed; all three crates pass rocrate-validator process-run-crate REQUIRED; tests and CI incl. R green

## Artifacts

## Findings

- Hands-on at 802b3e4 (uv env, detk-norm cpm on a 30-gene counts.csv), each crate checked with rocrate-validator 
  (--profile-identifier process-run-crate --requirement-severity REQUIRED): all three passed, 0 issues.
  - `detk-norm cpm counts.csv > n.csv`: module JSON out_file_path "stdout" (the marker, as module_schema.json documents);
    the CreateAction has object ../counts.csv and no result; no @id ends in stdout; hasPart is [../counts.csv].
  - `detk-norm cpm -o out.csv counts.csv`: result [../out.csv], hasPart [../counts.csv, ../out.csv].
  - `detk-norm cpm -o <abs>/stdout counts.csv`: out_file_path and argv recorded "./stdout"; result [../stdout], a File, in hasPart (DETK-0420 option 1 as accepted).
- Local: `uv run pytest` 2507 passed, 142 skipped; tests/report/test_crate.py 23 passed, 0 skipped, so both rocrate-validator cases ran; ruff check and ruff format --check clean.
- CI on 802b3e4: all green, including "test with R (bioconda)" (24m40s), CodeQL, docs build (strict), combined coverage.
- The diff stays within scope (crate.py, report.py via DETK-0420, test_crate.py, CHANGELOG). The CHANGELOG entry is under Fixed and cites #147 and DETK-0420.
- The `recorded` exception is right: record checksums the outputs it lists, so a recorded "stdout" is a real file (tested).
- Not blocking: `-` (a standard stream) is still not left out of the crate's results. No detk command records `-` as an output today; this is already noted in DETK-0420's consequences.
- Not blocking, and older than this PR: the crate.py module docstring says each File carries sha256/contentSize, but only files that detk-util record checksummed do (../out.csv and ../stdout have neither). This is a docstring precision issue for a later docs pass, not a defect here.

## Questions
