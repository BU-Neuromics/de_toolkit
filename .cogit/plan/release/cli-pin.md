---
kind: task
objective: 'Tests pin how every detk-* command parses its command line, written so they outlive docopt-ng, before the parser is replaced (DETK-0001)'
acceptance:
  - 'for each of the 11 entry points and every subcommand, tests run command lines through the command''s own entry point and assert the arguments it acts on: each positional, each option in its short and long form, each default, the shared options added by common.py, and repeated or multi-valued options'
  - 'invalid command lines (unknown subcommand, unknown option, missing positional, bad value) are pinned as a non-zero exit with the offending argument named; --help is pinned as exit 0 and naming every option. Whether its layout is pinned waits on Adam''s answer to whether the --help layout is part of the 1.0 promise'
  - 'the docopt behaviours detk relies on are each pinned by name in a test, including long-option prefixes (--out for --output) and the `[default: ...]` values, so DETK-0023''s choice can be weighed against them'
  - 'the expected values live in one table per command, and the tests reach the parser through one small adapter, so release/cli-migrate changes the adapter and not the expectations'
  - 'the tests pass on main as it is (docopt-ng), import nothing from docopt, and run in CI without R'
from: [DETK-0001]
scope: [tests/cli/, +tests/conftest.py]
prev: [DETK-0001]
---

# Pin each command's parsing in tests

## Implementation plan

- [ ] @developer Write `tests/cli/`: per-command tables of command lines and the arguments each yields, the invalid lines and their exits, the named docopt behaviours, through one adapter at the point each `main` dispatches; no change to `de_toolkit/`; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: every entry point and subcommand covered, expectations independent of docopt, nothing pinned that the 1.0 promise does not cover <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B). Needs no
library choice, so it can start before DETK-0023 is answered. If a
behaviour turns out to be accidental (it looks like a docopt quirk no user
would rely on), the developer records it as a question for Adam rather
than pinning or dropping it.
