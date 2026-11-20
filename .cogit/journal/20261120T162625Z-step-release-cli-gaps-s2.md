---
kind: step
time: 2026-11-20T16:26:25Z
by: DETK/reviewer
node: release/cli-gaps
step: s2
branch: review/cli-gaps
verdict: changes
commits: []
decisions: [DETK-0151]
---

# Changes asked: Review the exit codes and messages from an agent's side: each failure class gives its code and a cause to act on

## Summary

Changes asked: detk-filter's usage checks (group without column data, unparsable expression, unknown column) exit 2 with an actionable cause; wrapr's R error names a deleted temp dir and loses a wrapped R error line. DETK-0151 Proposed (Python 3.11 intermixed options).

## Artifacts

## Findings

Checked: diff origin/main...a672bb7; local suite on 3.13 (2036 passed, 78 skipped); PR #98 CI green on a672bb7, all jobs, including "test with R (bioconda)" (2092 passed, 22 skipped; tests/cli/test_cli_exit_codes.py ran, R-gated test included). Probed every failure class by hand on 3.13 and 3.11. Most of it holds up for an agent: argparse errors and number options exit 2 naming the option; a design without counts or that can't be parsed exits 2 with the usage; a missing file, missing Rscript, a missing R package or a failing step exits 1 with one `<prog>: error: <cause>` line last on stderr and the --verbose hint; the umbrella passes the code on; help ends with the codes; --column-data is now a usage error (exit 2) naming it.

Changes asked (s3, or before it):

1. detk-filter, a group expression with no column data (`detk-filter 'mean(group[cond]) > 1' counts.csv`): exits 1. This is a usage check detk makes after parsing (DETK-0031, the node's acceptance: "a design without counts where one is required" is the same kind), so raise UsageError and exit 2 with the usage. The message is already good. Pin it in test_cli_exit_codes.py.
2. detk-filter, a <command> that does not parse (`detk-filter 'garbage(((' counts.csv`): exits 1 with the cause `LexToken(WORD,'garbage',1,0)`. The argument is wrong, so exit 2 (DETK-0150 treats an unparsable design the same way), and the cause should say the filter expression could not be parsed and where (the token and its position). An unknown group column (`'mean(group[nope]) > 1' counts.csv cov.csv`) gives the cause `'group'` (a bare KeyError); name the missing column, and use exit 2 by DETK-0150's rule for an unknown design column. Pin one of each.
3. wrapr's RExecutionError names `[R's output is in <dir>]`, but without --routput-dir that is the TemporaryDirectory, deleted when the command exits, so the agent is sent to a path that no longer exists. Name the directory only when --routput-dir was given; otherwise say "rerun with --routput-dir DIR to keep R's output".
4. The R cause line: R often splits `Error in f(x) :` and the message across two lines; `next(e for e in errors if e.startswith("Error"))` keeps only the first, so the cause is lost. Join the Error line with its indented continuation lines. Tighten test_failing_r_step_exits_1_with_its_cause to assert "fails on purpose" is on the last line (it only asserts "R" now).

Not blocking (nits / pre-existing):
- An invalid design's cause shows nested tuple reprs: `Invalid design, detk formula syntax could not parse ("Misspecified column ... ('Unable to evaluate factor `nope`. ...',)",)`. Unwrapping the inner message would read better.
- Non-numeric counts in detk-norm deseq2 give `loop of ufunc does not support argument 0 ...` (pre-existing; a data check belongs to another node).
- detk-filter prints ply's `WARNING: 4 shift/reduce conflicts` on stderr every run (pre-existing; it isn't the last line, so the cause rule holds).

What the developer flagged:
(1) Python 3.11, an option before an optional positional (`detk-stats summary counts.csv -o out.csv cov.csv`): reproduced on 3.11.16 for stats summary, stats pca and detk-filter (exit 2, unrecognized arguments); 3.13 accepts it. This breaks the 1.0 CLI promise (DETK-0001) on 3.11, and the line worked under 0.9's docopt. It predates this PR. Recorded as DETK-0151 (Proposed): recommend a separate small node before 1.0 that makes the leaf parsers intermixed (DetkParser(intermixed=True), as gather already is), with a cli-pin row per command that has an optional positional (filter, stats summary/pca, transform rlog, wrapr run), run in the 3.11 job. Option B is to do it here in s3. Not a blocker for this node.
(2) detk-filter group with no column data exits 1: see change 1.
(3) --column-data still in the repo: the cli_tables/test_cli_behaviours pins are the acceptance's own pins of the removal; .cogit/ is the record. The two uses at CHANGELOG lines 109-110 sit in cli-migrate's 1.0 metavar row, describing a metavar change to an option this same release removes. Under +CHANGELOG this node edits only its own rows, so leave them; drop the two clauses when release/cut finalizes the 1.0 CHANGELOG (for Adam).

## Questions

- DETK-0151 On Python 3.11 an optional positional after an option is rejected: fix before 1.0, and where (#99)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
