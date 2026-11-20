---
kind: step
time: 2026-11-20T17:08:51Z
by: DETK/reviewer
node: release/cli-gaps
step: s2
branch: review/cli-gaps
verdict: approve
commits: []
decisions: []
---

# Approved: Review the exit codes and messages from an agent's side: each failure class gives its code and a cause to act on

## Summary

Approved (second review, 159a2e4): changes 1-4 done and pinned; DETK-0151 intermixed parsing works on 3.11 with 5 pins; the one-character token fix is sound. CI green incl. R and 3.11.

## Artifacts

## Findings

Second review of s2, at code head 159a2e4. Approved.

Checked: diff 3c9e88f..159a2e4. PR #98 CI is green on 159a2e4: "test with R (bioconda)" 2106 passed / 22 skipped, with test_cli_exit_codes.py run in full including the R-gated tests; "test (python 3.11)" 2049 passed / 79 skipped, with the DETK-0151 pins in test_cli_behaviours.py run. The local suite on 3.11.16 passes (2049 passed, 79 skipped). Each case below was run by hand on 3.13 and 3.11.

1. Group expression without column data: exit 2 with the usage; the cause names the column and <cov_fn>. Pinned.
2. An expression that doesn't parse: exit 2 with the expression and the token and position (`unexpected 'garbage' at position 0`, `illegal character '$' at position 14`, `it ends before the expression is complete`). An unknown column: exit 2, naming it and listing the column data's columns. Pinned.
3. wrapr names the directory only when --routput-dir was given; otherwise "rerun with --routput-dir DIR to keep R's output". Both are pinned, R-gated, and passed in the R job.
4. r_error_cause joins `Error in f(x) :` with its indented continuation lines. It has a unit test (4 cases), and the R-gated test checks the actual message `Error in f(1) : this script fails on purpose`.

DETK-0151 (intermixed): DetkParser._parses_intermixed makes every leaf parser that has a `?`/`*` positional intermixed. The rule is automatic, so a future optional positional is covered without a flag. 3.11 now accepts `counts.csv -o out.csv cov.csv` for filter, stats summary, stats pca, transform rlog and wrapr run (5 parse pins, run in the 3.11 job). Behaviour that must not change still holds on 3.11: an extra positional, an option given twice, rlog's <design>-without-<cov_fn> check, and `--` (unrecognized, the same as on main) all exit 2. tests/report has its natural argument order back.

The unasked one-character token fix (t_WORD `+` to `*`): accepted. It is a real bug (`mean(c[A]) > 1`, or any one-letter column or group, was a lex error), it sits in a scoped file, the CHANGELOG lists it, and a test covers it. WORD tokens are only letters, digits, `_` and `.`, so the change can't swallow an operator, a bracket or a number (a number still can't start a WORD). The only new token is a lone `.`, which now reaches the unknown-column message instead of a lex error. It's harmless.

Not blocking (follow-ups):
- A group value missing from its column (`mean(cond[Z]) > 1` when cond has only A and B) exits 0 and writes a header-only file, with no warning. It predates this PR. It could be a usage error naming the column's values, by the same rule as an unknown column; suggested for a later node.
- An invalid design's cause still carries a tuple repr from the inner error (`... check term names. ('Unable to evaluate factor `nope`. ...',)`). It reads better than before.
- CHANGELOG lines 109-110 (cli-migrate's metavar row) still name `--column-data`; release/cut should handle it.

## Questions
