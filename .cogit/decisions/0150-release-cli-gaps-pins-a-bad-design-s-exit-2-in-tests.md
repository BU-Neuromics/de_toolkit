---
template: adr
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release/cli-gaps, step: s1}
applies: [release/cli-gaps]
issue: 96
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's delegation via the driver session, 2026-11-20: Option A, cli-gaps edits the formula pin; every InvalidDesignException exits 2; follows directly from DETK-0031 and stays within the 1.0 scope"}
---

# release/cli-gaps pins a bad design's exit 2 in tests/formula, outside its scope

- Proposed by: the release/cli-gaps developer session, 2026-11-20 (step s1)

## Background

DETK-0031 (Accepted) sets the exit codes: 0 success, 2 usage error, 1
anything else. release/cli-gaps' acceptance counts "any usage check detk
makes after parsing, such as a design without counts where one is
required" as a usage error, exit 2. `tests/formula/test_formula_pins.py::
test_de_cli_exits_on_bad_design` (from release/formula-pin) pins the
opposite: a bad `detk-de` design exits **1** and the cause is a log
record (caplog). `tests/formula/` is not in release/cli-gaps' scope.

The test covers four designs: two without `counts` ("category ~
cont_cov"), one naming a column that is not in the column data
("counts ~ nope"), and one with no `~` ("category + counts"). All four
raise `InvalidDesignException` before R is needed.

## Context

- The acceptance cannot be met without changing the pin: the same command
  line cannot exit both 1 and 2.
- After the change the cause is printed by the one handler
  (`common.cli_main`) on stderr, not logged, so the pin reads stderr
  (capsys) instead of caplog.
- release/r-design-names runs in parallel and may edit tests/formula; the
  edit is one test function, so a merge conflict there is small.
- Which errors count as usage: the acceptance names the design without
  counts. A formula detk cannot parse ("category + counts") is the same
  kind: the `<design>` argument is wrong. A design naming a column that
  is not in the column data ("counts ~ nope") is a mismatch between the
  argument and a file; either code is defensible.

## Options

### Option A: release/cli-gaps edits the pin; every InvalidDesignException exits 2 (recommended)

The pin expects exit 2 and the cause on stderr for all four designs.
`InvalidDesignException` is one class, raised only for a design that
cannot be used, so the handler maps it to 2 without inspecting messages.
An agent reads 2 as "fix the command line", which for all four cases
means "fix the design", the right action even for an unknown column
(the user names a column that exists or fixes the column data).

### Option B: edit the pin, but an unknown column exits 1

Split `InvalidDesignException` (or match messages) so a column missing
from the column data is "bad input", exit 1. More precise in principle;
needs a new exception class in common.py/formula.py (formula.py is not
in scope either) and a two-way pin.

### Option C: leave tests/formula alone; a separate node changes it

release/cli-gaps cannot pass CI until that node lands, or it skips the
pin; this blocks the node on a one-function edit.

## Decision

Recommended: Option A. The edit is the direct consequence of an accepted
decision (DETK-0031) and the node's own acceptance; it is one test
function; and one exception class mapping to one code is the simplest
rule to keep. Awaiting the driver's / Adam's answer; the node's PR branch
carries Option A's edit.

## Consequences

`tests/formula/test_formula_pins.py` joins release/cli-gaps' scope for
this one test. If Option B is chosen, s3 adds the split and the second
pin; if C, the edit is reverted from the branch and moved to a new node.
