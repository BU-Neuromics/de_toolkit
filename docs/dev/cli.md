# Adding a command or an option

Every detk command parses its command line with argparse (DETK-0023): a
`build_parser()` in its module returns a `DetkParser` (`de_toolkit/common.py`),
and `main(argv)` calls `parse_cli(build_parser(), argv)`. The help a user
sees is what that parser formats, so the parser is the interface: change the
parser, and the help, the shell completion scripts and the docs follow from
it. The comment above `DetkParser` in `common.py` says what the help holds,
in which order; that structure and the facts in it are the 1.0 promise
(DETK-0025 Option B, stated on the home page under Stability), so a change
to them is a change to the CLI and goes in the CHANGELOG.

## An option

Add it to the subcommand's parser in `build_parser()`, before
`add_common_options(sub)`:

```python
sub.add_argument(
    "--min-count",
    metavar="N",
    default="10",
    help="Keep the features with at least N counts in some sample",
)
```

- **metavar**: one of the words the help uses for a kind of value: `FILE`,
  `DIR`, `N`, `CHAR`, `COL`, `COLS`, `FMT`, `REGEX`, `WHAT`, `BOOL`, `NAME`
  or `TEXT` (the list and what each means are in
  `tests/cli/test_cli_help_sections.py`). A new kind of value adds a word
  there and a line to the CHANGELOG.
- **default**: give it as the value the command acts on; the help prints
  `(default: 10)` after the description by itself, and `(choices: a, b)` for
  an option with `choices=`. Do not write either into `help=`.
- **help**: one line, a sentence without its full stop.
- A flag is `action="store_true"`. An option given twice is a usage error
  (`DetkParser` makes it one); a value detk has to check after parsing (a
  number out of range, two options that exclude each other) raises
  `UsageError` from `common.py`, or returns a message from the parser's
  `validate=`, so the command exits 2 with its usage (DETK-0031).
- The positionals are written `<name>`, docopt style:
  `sub.add_argument("counts_fn", metavar="<counts_fn>", help=...)`. The
  usage line is built from them, one line per subcommand.

## A subcommand

Add it with `add_subcommands(parser).add_parser(...)`, as every module does
(see `SUBCOMMANDS` and `build_parser()` in `de_toolkit/norm.py`):

```python
sub = subs.add_parser(
    "cpm",
    help="Counts per million: library size normalization times 1e6",
    description="Perform Counts Per Million normalization on ...",
    examples=[("Counts per million of counts.csv", "detk-norm cpm -o cpm.csv counts.csv")],
)
sub.add_argument("counts_fn", metavar="<counts_fn>", help="Counts file: ...")
add_common_options(sub)
```

`help` is the one line the command's own help lists the subcommand with,
`description` the text its help starts with. Every subcommand has at least
one example, a `(what it does, command line)` pair; the help prints them
under `examples:`, and `tests/cli/test_cli_help_sections.py` parses each
one and runs it where its test data has the files it names. Dispatch on
`args.subcommand` in `main`.

## A command

A new `detk-<name>` command is a module `de_toolkit/<name>.py` with
`build_parser()` and a `main(argv)` decorated with `@cli_main` (the exit
codes), and:

- an entry point in `[project.scripts]` of `pyproject.toml`;
- a line in `MODULE_COMMANDS` in `common.py`, so `detk <name> ...` runs it;
- a report view if it records module JSON (`docs/report.md`).

## What else changes with the parser

Run these after a change, and commit what they rewrite:

```console
$ uv run python -m de_toolkit.completions._generate   # the shell completion scripts
$ uv run python tests/docs/docs_usage.py              # the usage blocks of docs/tools/
```

and update by hand:

- `tests/cli/cli_tables.py`: the table of every command line's meaning,
  which the tests check the parser and its help against;
- the command's page under `docs/tools/` (a new subcommand needs a usage
  block there: copy its usage line into a ```` ```text ```` block and the
  script above fills it in) and `docs/tools/index.md` for a new command;
- `skills/detk/` where the skill shows the command;
- the CHANGELOG.

`tests/completion/`, `tests/docs/test_docs_usage.py` and
`tests/skills/test_skills.py` fail until the scripts, the usage blocks and
the skill match the parser.
