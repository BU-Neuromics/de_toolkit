---
kind: step
time: 2026-11-20T13:34:27Z
by: DETK/reviewer
node: release/cli-migrate
step: s2
branch: review/cli-migrate
verdict: approve
commits: []
decisions: []
---

# Approved: Review the pattern before it is copied: cli-pin passes for detk-norm, help follows DETK-0025 Option B and reads well for an agent

## Summary

Approved: the argparse pattern (DetkParser, parse_cli, table-built build_parser) is right to copy; help follows DETK-0025 B, exit codes 0/2/1, --version per DETK-0033; three items for s3 in the shared test and parse_cli; the developer's three flagged choices need no decision

## Artifacts

## Findings

Checks run on e64ab1b:
- `uv run pytest`: 1780 passed, 235 skipped. `ruff check` and `ruff format --check` are clean.
- CI on e64ab1b is green, every job: test (python 3.11/3.12/3.13), **test with R (bioconda)**, ruff, docs build (strict), runtime dependencies only, combined coverage, CodeQL.
- All five norm examples run in `test_examples_run_where_test_data_allows`. None is skipped.
- I ran `detk` and `detk-norm` by hand on the edge cases: no args, unknown subcommand, missing positional, unknown option, an option given twice, `-vq`, `--outp=` prefix, `-oFILE`, `--`, an extra positional, and `--version` at each level and as `-o`'s value.

What holds (the pattern is right to copy):
- argparse use: one `build_parser()` per module, built from a table (`SUBCOMMANDS`). The shared pieces live in `common.py`: `DetkParser`, `add_common_options`, `add_subcommands` and `parse_cli`. `main` reduces to `parse_cli(build_parser(), argv)` plus attribute access. The `_arg` shim keeps `set_logging`, `make_cli_count_obj` and `write_output` working for the docopt modules until s3. s3 should remove it with docopt.
- DETK-0025 Option B: help sections come out in the promised order (description, usage, positional arguments, options, common options, examples). Every option states its metavar and `(default: x)`, and `(choices: ...)` where it has them. Each argument has a one-line description. Each subcommand has an example. The tests check each example parses to its subcommand and run it on test data. Help is fixed at 80 columns, so its output is reproducible. It reads well for an agent: the subcommand list carries one-line help, and the shared `_LENGTHS_NOTE` keeps fpkm and tpm consistent.
- DETK-0031 exit codes: usage errors exit 2 and end with `Run '<prog> --help' for help.` `-h`, `--help` and `--version` exit 0. Runtime failures keep `sys.exit(1)`.
- DETK-0033 item 2: `--version` uses argparse's `action="version"`.
  - It prints the version at command level, at subcommand level and after positionals.
  - `-o --version` is a parse error naming `-o`.
  - `anything --version else` is an error naming `anything`.
  - New pins cover all of these. The other three DETK-0033 items are s3's.
- Pins changed on purpose: the umbrella now dispatches enrich, report and util, and its help lists all ten module commands (gap 1). The `--version` pins changed as above. The adapter stops at `parse_cli`, and the tables are otherwise unchanged.

The developer's three flagged choices. All three are fine within the accepted decisions, and none needs a decision record:
1. Dropping the `detk version: X` help header: fine. DETK-0025 B starts help with the description. Adam's reply on DETK-0025 says item 6 (version handled before parsing, with the header) is "fine", not a promise. The version stays available through `--version`. Mention the removal in the s3 CHANGELOG entry.
2. Keeping docopt-style positional names (`<counts_fn>`): fine. Gap 3 and the acceptance cover option metavars only. `<counts_fn>` matches the docs, the skill, the descriptions and the cli-pin tables. argparse's errors read clearly with it ("the following arguments are required: <counts_fn>").
3. Keeping the three docopt behaviours (an option given twice rejected, `--` rejected, an unknown option reported before a missing positional): fine. These are what the acceptance requires: cli-pin expectations stay unchanged except where changed on purpose, and dropping a pinned behaviour is a question for Adam. Relaxing any of them would be the decision. Keeping them needs none.

Asked for s3 (not blocking the pattern; all three are in the shared code or the shared test, so s3 can fix them once):
1. `test_cli_help_sections.py::test_help_sections_in_order` requires all five headings. argparse leaves out an empty section, so a subcommand with no positionals fails the test. I built `detk-report clean` this way: its help has no "positional arguments:" heading. Make the test check the order of the headings present and require only description, usage, options and examples. A subcommand with no positionals should not get a dummy one.
2. `METAVARS = {FILE, DIR, N, CHAR}` is a closed set. The acceptance asks that files take FILE, directories DIR and numbers N. It does not say every metavar must be one of the four. Today's usage blocks also use FMT (10), FIELD, COL/COLS/COLNAME, REGEX, WHAT, BINS, PROCS and others for values that are none of those. Two ways to fix the test:
   - enforce FILE/DIR/N for file, directory and number options and accept another single upper-case word otherwise;
   - or have s3 pick the extra metavars and list them in the test and the CHANGELOG.
   Either way, don't force a format, column or regex option into FILE or N. Unifying FMT, PATH and RDA is still gap 3's work.
3. Some errors raised in a subcommand are reported by the top-level parser:
   - an extra positional (`detk-norm deseq2 c.csv extra`);
   - `--` after a subcommand.

   The error then prints every subcommand's usage line, says `detk-norm: error: ...` and points to `detk-norm --help` instead of the subcommand's help. With util's or stats' many subcommands that is a wall of text for an agent. In `parse_cli`, raise the `--` error on `leaf`. Report leftovers on `leaf` too: use `parse_known_args`, then `leaf.error("unrecognized arguments: ...")`. Unknown options are already reported this way.

Nits:
- `detk-norm --help` lists only `--version` under "common options", while the common options are taken by each subcommand. A one-line group description on the top-level parser would stop an agent concluding there are none. One possible line: "each subcommand also takes the common options; see detk-norm <subcommand> --help".
- The `_detk_seen` marker is removed only by `parse_cli`. Any code calling `parse_args` directly will see it in the namespace. Keep `parse_cli` the only entry point, as the docstring says.

## Questions
