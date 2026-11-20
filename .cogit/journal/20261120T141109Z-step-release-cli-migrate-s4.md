---
kind: step
time: 2026-11-20T14:11:09Z
by: DETK/reviewer
node: release/cli-migrate
step: s4
branch: review/cli-migrate
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR, including the R-gated tests in CI and the airway run

## Summary

Approved: all acceptance items met; R job green with the airway example on 822612c; s2 asks folded in; closed metavar list fine within delegation; DETK-0070 supersedes DETK-0010; DETK-0081 Proposed (applies to release/cut) for three inert options, not blocking

## Artifacts

## Findings

Checks on 6cc969a. Its code is identical to 822612c's; the only difference is files under .cogit/.
- Local: `uv run pytest` gives 1950 passed and 74 skipped (R is not on this machine). `ruff check` and `ruff format --check` are clean.
- CI on 822612c is green on every job. **test with R (bioconda)** ran 2004 passed, 20 skipped, and `tests/example/test_airway_example.py` passed: the airway example (`run.sh --skip-enrich`, unchanged) ran end to end on the migrated CLI. CI on 6cc969a was still running the R job when I recorded this; every other job there is green.
- I ran each command by hand on the edge cases. All usage errors exit 2 and point at the help of the subcommand named; help and `--version` exit 0; runtime failures exit 1. Cases checked:
  - rlog with a design and no cov_fn;
  - `stats -f bogus`;
  - gather `--format` and `--on-mismatch` outside their choices;
  - `outlier trim`;
  - an extra positional;
  - `--` after a subcommand;
  - an option given twice, including in gather's intermixed form;
  - `detk report`, `detk util` and `detk enrich` through the umbrella;
  - a prefix match (`--outp=`).
- I read the help of every command and subcommand (about 1500 lines). It is consistent and reads well for an agent.

Acceptance, item by item:
- **Argparse in all 11 entry points; docopt-ng gone.** Met. docopt is not in pyproject.toml, uv.lock or the code, and `de_toolkit/test_docopt.py` is removed.
- **cli-pin unchanged except on purpose.** Met. Changed on purpose: the umbrella pins, `--version`, the DETK-0033 pins, the metavars and exit 2. The rest of tests/cli is unchanged apart from the adapter.
- **DETK-0025 Option B help.** Met:
  - the sections come in order, and an empty positional section may be left out (my s2 ask 1);
  - every option has its metavar, default, choices and a one-line description;
  - every subcommand has an example; each example parses, and runs where test data allows. The R examples run in CI's R job.
- **Umbrella `detk` (gap 1).** Met. It runs all ten module commands and its help lists them.
- **Metavars (gap 3).** Met. FILE, DIR and N are used for files, directories and numbers, including filter's `<out_fn>`, `--rda` and `--routput-dir`. The CHANGELOG lists each rename.
  - The developer's closed list adds CHAR, COL, COLS, FMT, REGEX, WHAT and BOOL. That is within the acceptance and the delegation: the acceptance fixes only FILE/DIR/N, and the list is written down in the test and the CHANGELOG. No decision record is needed. My s2 ask 2 is resolved.
- **DETK-0010 → DETK-0070.** Met: the skill test parses through `build_parser()` and `parse_cli`, and the usage blocks in commands.md are regenerated and checked. DETK-0070 has since been accepted and supersedes DETK-0010 (52ff89f).
- **DETK-0033 Option A.** Met. All four behaviours are parse errors or removed, each pinned in tests/cli/ and in the CHANGELOG. `test_rlog_design_without_cov_fn` is un-skipped and inverted.
- **Suite, R job, ruff and airway.** Met (see above).
- **DETK-0031.** Usage errors exit 2, and the CHANGELOG marks this as a breaking change. The rest of DETK-0031 (one handler for every other failure) is release/cli-gaps' job.
- **s2 asks.** All three are folded in. Errors are reported by the subcommand's parser (`leaf`), and the top-level "common options" section has a line pointing to the subcommand help.

Not blocking:
- `pyproject.toml`'s comment on the E402 ignore still says "docopt usage string and cmd_opts". The ignore itself is still needed: module docstrings and tables come before the imports. Reword the comment whenever someone next touches that file (the developer noted it too).
- `docs/tools/*.md` still hold docopt-era usage blocks. That is release/cli-docs' acceptance, not this node's.

Recorded for Adam: **DETK-0081 (Proposed, #85; applies to release/cut, not to this node)**. Three options in help don't do what their help says. None of them worked under docopt either; the migration made their help explicit.
1. `detk-transform vst|rlog --rda` is never read.
2. `detk-stats summary --color-col` is never read, although the subcommand's help example and `examples/airway/run.sh` use it.
3. `rlog --blind` passes its value on as a string. `--blind False` keeps the blind `~ 1` design and leaves out the column data, so a non-blind rlog with the user's design can't be asked for.

I recommend Option A: make each do what its help says, as DETK-0029 did for `--size-factors`. That would be a follow-up before release/cut, possibly a step in release/cli-gaps, which already edits these modules. It does not block this PR.

## Questions
