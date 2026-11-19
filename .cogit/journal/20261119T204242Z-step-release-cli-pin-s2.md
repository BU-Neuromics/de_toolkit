---
kind: step
time: 2026-11-19T20:42:42Z
by: DETK/reviewer
node: release/cli-pin
step: s2
branch: review/cli-pin
verdict: changes
commits: []
decisions: []
---

# Changes asked: Review the PR: every entry point and subcommand covered, expectations independent of docopt, help facts pinned and wording left free (DETK-0025 Option B)

## Summary

Changes asked: help-default check is vacuous for 12 options (substring match); otherwise coverage, adapter, invalid lines, behaviours and umbrella pins are sound

## Artifacts

## Findings

Checks run on b4f8277: `pytest tests/cli`: 1,298 passed, 1 skipped (DETK-0033). Full suite: 1,664 passed, 63 skipped (R-gated; R isn't on this machine, so "test with R (bioconda)" in CI still pending). `ruff check` and `ruff format --check` are clean. CI's Python and lint jobs are green.

What holds:
- Coverage: every `--option` in each module's usage text is in the tables, and the defaults line requires every table option to be one the parser reports. The only gaps are `--json`/`--html`, which appear only in detk-stats' module prose and not in any usage. That stale doc text is outside this node's scope.
- Nothing in tests/cli imports docopt. The parser is reached only through `cli_adapter.py`, and the tables are parser-neutral.
- A mutation check bites: changing transform plog `--base` `[default: 10]` to 2 fails 20 tests.
- The invalid lines, the named behaviours (including `--out` ambiguous, `--outp`, filter `--column-data`, norm deseq2 `--size-factors`), the umbrella pins and the console-script parity all match the acceptance. The divergences from the node's wording are disclosed in the PR body.

Change asked (blocking, help facts per DETK-0025 B):
1. `test_cli_help.py::test_subcommand_help_states_options` checks a default with `opt.default in e`, a substring test on the option's help entry. For 12 options it passes even when help stops stating the default, because the value appears elsewhere in the entry. I checked this by stripping `[default: ...]` from each entry; these still pass:
   - detk-stats `--format` default csv (all 8 subcommands): the value is in "either csv or table"
   - detk-util gather `--format` auto and `--on-mismatch` error: the value is in the choices list
   - detk-util annotate `--map-to` all: the value is in the description
   - detk-enrich fgsea `--idcol` 0: the value is in the description

   Short single-digit defaults are also fragile (`-c` pseudocount 1). Please tie the default to its statement without pinning wording. One option: assert `re.search(rf"default\W+{re.escape(opt.default)}\b", e, re.I)`, which both docopt's `[default: X]` and argparse's `(default: %(default)s)` satisfy. If you think requiring the word "default" goes beyond DETK-0025 B, record that as a question for Adam instead.

Notes, not blocking:
- Missing positional: the check passes because the usage line names every positional, so it can't tell which one is missing. The PR discloses this, and it's fine as a pin of today's behaviour. release/cli-migrate should tighten it once the parser names the missing one.
- detk-stats summary `--column-data` is also marked DEPRECATED in its usage but has no warning pin, unlike filter's. The acceptance names only filter's, so this is optional.

## Questions
