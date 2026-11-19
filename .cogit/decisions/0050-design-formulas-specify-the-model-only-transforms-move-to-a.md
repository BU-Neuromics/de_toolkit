---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/formula-rename, release/augment]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: \"the formula should just specify models, and nothing else. I wonder instead if detk should provide some simple augmentation functions\"; then \"yes\" to the driver's summary of the consequences"}
---

# Design formulas specify the model only; transforms move to a column data augmentation command

- Proposed by: the planning session, 2026-11-19, to record Adam's change
  of mind on DETK-0028, relayed by the driver session

## Background

DETK-0028 was accepted earlier on 2026-11-19 as Option B: a fixed set of
transforms (log, log2, and so on) inside design formulas, computed by
detk and recorded in provenance. DETK-0047, still Proposed, laid out the
set, names, edge cases and provenance for that. The same day Adam
reconsidered.

## Context

Adam, 2026-11-19, relayed by the driver session: "I think I changed my
mind about the functions in formulas. This mixes concerns -- the formula
should just specify models, and nothing else. I wonder instead if detk
should provide some simple augmentation functions, like adding a column
with a constant, logs with options that control what should happen to
zero values and pseudocounts, parameters for scaling, e.g. having an
option that scales values to be between zero and one."

The driver summarized the consequences (below) and Adam answered "yes"
to planning them. He confirmed that "scale" means a z-score using the
sample standard deviation (n-1).

## Options

### Option A: formulas specify the model only; a separate command augments the column data

No transform of any kind in a formula. A separate detk step writes a new
column data file with the derived columns, and records itself in the
module JSON and the Process Run Crate like any other step.

### Option B: transforms in formulas (DETK-0028 as accepted)

Superseded by this record.

## Decision

Option A, chosen by Adam on 2026-11-19 (quoted in Context). This record
supersedes DETK-0028 and DETK-0047.

1. Formulas specify the model only. A term that is not a column of the
   column data file and looks like a call (`np.log(x)`, `log2(x)`) is a
   `FormulaParseError` saying that formulas take column names only, and
   pointing to the augmentation command. A column whose name really is
   `log2(x)` still works as a column, as it does today.
2. `docs/formulas.md` drops the `np.log` pass-through claim.
3. A column data augmentation command adds derived columns: a constant
   column; logs, with options for the base, pseudocounts and what happens
   to zero values; and scaling, including min-max to [0, 1], centring and
   the z-score (sample standard deviation, n-1). It writes a new column
   data file and records itself like other detk steps. Its design (name,
   placement, options, column names, provenance) is DETK-0051, Proposed
   and Adam's.

## Consequences

- `release/formula-transforms` is replaced by `release/augment`, which
  builds the command once DETK-0051 is answered.
- `release/formula-rename` adds the error for a call in a formula and
  removes the docs claim. `release/augment` then names itself in that
  error and in `docs/formulas.md`.
- The R-safety fix from DETK-0047 item 5 does not depend on transforms.
  Every name in the resolved design that is not a syntactic R name is
  backtick-quoted before R's `formula()`, so a column data name that
  looks like a call is never run. It becomes its own node,
  `release/r-design-names`, and is recommended to Adam rather than
  decided by this record.
- `release/formula-pin`'s `np.log` pins keep pinning a failure; only the
  message text changes.
