---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release/cli-pin}
applies: [release/cli-pin, release/cli-migrate]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: accepts Option A on the developer session's recommendation; release/cli-migrate makes each of the four accidental behaviours a parse error or removes it"}
---

# Command line behaviours found while pinning: keep, reject or expose

- Proposed by: the developer session on release/cli-pin (step s1), 2026-11-19

## Background

`release/cli-pin` pins how every `detk-*` command parses its command line
today, so that replacing docopt-ng with argparse (DETK-0001, DETK-0023)
changes behaviour only where a pin is edited on purpose. The node's notes
say that a behaviour which looks accidental (a docopt quirk no user would
rely on) is a question for Adam, not something to pin or drop. Reading the
commands while writing the pins turned up four such behaviours. None is in
the list of CLI gaps DETK-0025 brought into 1.0.

## Context

What each does today (docopt-ng 0.9.0, main at a21a419):

1. **`detk-transform rlog <counts_fn> [<design> <cov_fn>]` accepts a design
   without a covariate file.** `detk-transform rlog c.csv d` parses with
   `design=d`, `cov_fn=None`: docopt matches the optional group partly. The
   run then fails later, or treats `d` as a design with no column data.
   argparse would need an explicit check to keep or to refuse this.
   *Not pinned*: `test_rlog_design_without_cov_fn` is skipped, citing this
   record.
2. **`--version` is answered even as another option's value.** Each `main`
   checks `"--version" in argv` before parsing, so `detk-norm deseq2 -o
   --version c.csv` prints the version and exits 0 instead of writing to a
   file named `--version`. DETK-0025 item 6 says handling `--version` before
   parsing is fine; this is the corner of it where it is not. *Not pinned*:
   only `--version` as an argument of its own is pinned.
3. **`detk-outlier trim` cannot be run.** `outlier.main` has a `trim`
   branch, but `cmd_opts` and the usage have no `trim`, so the command line
   is rejected with the usage. `tests/outlier/test_outlier.py` calls it only
   in a test disabled inside a string literal. *Pinned as rejected* (it is not in the usage, so
   no user can be relying on it).
4. **Choices are not checked by the parser.** `detk-stats -f/--format` lists
   `csv` and `table`, but any other value silently means csv. `detk-util
   gather --format` and `--on-mismatch` are checked by the command after
   parsing (non-zero exit naming the option). argparse `choices=` would make
   all three parse errors. *Pinned*: the choices in help, and gather's
   run-time rejections; `-f bogus` is not pinned either way.

Criteria: what an agent writing a command line can rely on; whether the
change is free with argparse or needs code; the 1.0 promise (DETK-0001).

## Options

### Option A: make each a parse error or remove it in release/cli-migrate

1. rlog requires both or neither of `<design>` and `<cov_fn>`.
2. `--version` is honoured only as an argument of its own (argparse's
   `action="version"` does this).
3. Remove the dead `trim` branch (or see B).
4. `choices=` on `detk-stats -f`, `detk-util gather --format` and
   `--on-mismatch`.

Each becomes a pin in `tests/cli/` when cli-migrate makes it. Small, and
mostly what argparse gives for free. A command line that worked by accident
(1, 4) stops working, but no documented usage does that.

### Option B: as A, but expose `detk-outlier trim`

As A, except `trim` gets a usage block and becomes a subcommand. New
surface promised from 1.0; its behaviour has no current test.

### Option C: keep today's behaviour and pin it

Pin all four as they are. Keeps argparse compatible with docopt's quirks,
which costs custom code for 1 and 2, and promises them from 1.0.

## Decision

Option A, accepted by Adam on 2026-11-19 (relayed by the driver session):
he accepts Option A on the developer session's recommendation.
release/cli-migrate makes each of the four behaviours a parse error or
removes it: rlog requires both or neither of `<design>` and `<cov_fn>`;
`--version` is honoured only as an argument of its own; the dead `trim`
branch of `detk-outlier` is removed; `detk-stats -f`, `detk-util gather
--format` and `--on-mismatch` reject values outside their choices when
parsing. Each becomes a pin in `tests/cli/` and a CHANGELOG entry. The
reason: each is unreachable or reachable only by a command line no
documentation shows, and argparse makes most of them correct without
extra code.

## Consequences

Under A or B, release/cli-migrate makes the changes and adds their pins
(un-skipping and inverting `test_rlog_design_without_cov_fn`, adding a
`--version`-as-value case and a choices case to the tables). Under C,
release/cli-pin adds the pins for 1, 2 and 4 now, and cli-migrate carries
the extra code.
