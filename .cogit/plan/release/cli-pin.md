---
kind: task
objective: 'Tests pin how every detk-* command parses its command line and what its --help states, written so they outlive docopt-ng, before the parser is replaced (DETK-0001, DETK-0025)'
acceptance:
  - 'for each of the 11 entry points and every subcommand, tests run command lines through the command''s own entry point and assert the arguments it acts on: each positional, each option in its short and long form, each default, the shared options added by common.py, and repeated or multi-valued options'
  - 'invalid command lines (unknown subcommand, unknown option, missing positional, bad value) are pinned as a non-zero exit with the offending argument named on stderr; the exact code is left to DETK-0031 and release/cli-gaps'
  - 'help is pinned as DETK-0025 Option B promises it: for every command and subcommand, -h and --help exit 0 on stdout, and the facts are pinned from the same tables: each positional and option with its metavar, default and choices, and the common options. The wording and layout are not pinned. Section order and examples are added to the pins by release/cli-migrate, which introduces them'
  - 'the docopt behaviours detk relies on are each pinned by name, including long-option prefixes (--out for --output), the `[default: ...]` values, detk-filter''s deprecated --column-data (accepted with a warning) and detk-norm deseq2''s --size-factors (accepted, writes nothing), so later nodes change those pins deliberately'
  - 'the umbrella `detk` command is pinned as it behaves today for each module command, including enrich, report and util, which it rejects (to be fixed by release/cli-migrate)'
  - 'the expected values live in one table per command, and the tests reach the parser through one small adapter, so release/cli-migrate changes the adapter and not the expectations'
  - 'the tests pass on main as it is (docopt-ng), import nothing from docopt, and run in CI without R'
from: [DETK-0001, DETK-0025]
scope: [tests/cli/, +tests/conftest.py]
prev: [DETK-0001]
issue: 70
visited: a21a419
---

# Pin each command's parsing in tests

## Implementation plan

- [x] @developer Write `tests/cli/`: per-command tables of command lines and the arguments each yields, the invalid lines and their exits, the help facts, the named docopt behaviours and the umbrella command, through one adapter at the point each `main` dispatches; no change to `de_toolkit/`; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: every entry point and subcommand covered, expectations independent of docopt, help facts pinned and wording left free (DETK-0025 Option B) <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B); help pins
per DETK-0025 (Option B, accepted 2026-11-19). Pins today's behaviour,
including the CLI gaps, so the nodes that fix them (cli-migrate, cli-gaps,
size-factors) show their changes as edits to these tables. If a
behaviour turns out to be accidental (a docopt quirk no user would rely
on), the developer records it as a question for Adam rather than pinning
or dropping it.
