---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/formula-rename]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: support a fixed set of transforms in 1.0 (the option read: 'Support a small whitelist (log, log2, etc.) in 1.0 and record it in provenance'); the set, naming, edge cases and provenance are DETK-0047"}
---

# Transforms such as np.log(x) in design formulas

- Proposed by: the planning session, 2026-11-19, at Adam's request: "I'm
  not sure on np.log(x) in formulas, can you find the rationale for
  including that and suggest whether it's a good idea?"

## Background

`docs/formulas.md` lists a fourth term type, "patsy": other patsy terms
"(e.g. interaction terms `binary_str:cat_str`, or expressions like
`np.log(cont)`). You do so at your own risk." The DETK-0024 study found
that the `np.log(cont)` half does not work: patsy-lite looks it up as a
column named `np.log(cont)` and fails. Interactions do work.

## Context

### Where the claim came from (git history)

- 2017-09-24 to 09-25 (`a4fb887`, `8ad008c`, `b17988d`, Adam):
  patsy-lite is written and documented. The first docs
  (`docs/patsy_lite.rst`) said: "You can try to put in expressions that
  patsy knows how to understand, like `np.log(cont)`, but you do so at
  your own risk and I'm going to pretend to not be responsible for what
  befalls you if you choose to do so." The lexer then had a
  `SIMPLETERM` token that passed such terms through to patsy unquoted.
  Running that 2017 version (`git show 3f34b11^:de_toolkit/patsy_lite.py`)
  on `y ~ np.log(x) + g[a]` gives the columns `Intercept`,
  `C(g, Treatment('a'))[T.b]`, `np.log(x)`. So transforms worked, as a
  convenience inherited from patsy and disclaimed from the start.
- 2018-08-21 (`3f34b11`, "fix for #34, . illegal in metadata column
  names"): to allow column names with dots (R-style names such as
  `fld.cont`), the fix added `quote_var`. It wraps any name containing
  `#`, `.`, `(`, `)`, `[`, `]` or `@` in `Q("...")`. That also quotes
  `np.log(x)`, which has broken transforms since then. Nothing in the
  repository records that this was intended; the docs were not changed.
  (#34 here is the 2018 tracker's number. Today's GitHub #34 is an
  unrelated 2026 PR.)
- 2026-08-11 (`399e3b0`, the MkDocs migration): the text was carried
  over in shorter form into `docs/formulas.md`, without testing it.
- No issue or PR discussion of transforms was found beyond these
  commits. The tests check only that the translation string contains
  `Q("np.log(x)")`, which is why the breakage went unnoticed.

### Trade-offs for an agent-facing 1.0 CLI

- **For transforms:** a log or scaled covariate is common in DE designs
  (for example log library size or a scaled age). Writing it in the
  formula is concise and familiar from R and patsy.
- **Against:**
  - *Explainability.* A transform written in the formula is invisible
    in the column data. A transformed column in the column data file is
    an explicit input, recorded in the RO-Crate provenance, and is the
    same in R and Python. detk's aim (Adam, 2026-11-18) is reliable,
    explainable agent-written analyses.
  - *Names.* The output columns would be named `np.log(x)` (with the
    DESeq2 statistics appended), and R has to accept them as column
    names.
  - *Code execution.* Both engines evaluate Python in formula terms.
    patsy ran `__import__('os').getpid()` from a formula. formulaic ran
    `len(str(x))`; it refused that particular `__import__` call on syntax
    alone. A design string would become code, which matters for a CLI
    driven by agents.
  - *Promise.* Under the 1.0 promise, whatever is supported has to keep
    working. A pass-through of "whatever the engine understands" ties
    the promise to formulaic's expression language.
  - *Column names.* A pass-through has to tell `np.log(x)` apart from a
    column with a dot in its name, the #34 case. That can be done by
    checking the column data first, but it is a second rule to explain.

## Options

### Option A: remove the claim, and say what to do instead (recommended)

`docs/formulas.md` drops the `np.log` example. It keeps interactions
(`a:b`, `a*b`), which work and are pinned. A formula term that is not a
column gets an error that says to add the transformed column to the
column data file. No behaviour changes: transforms do not work today.

### Option B: a small, named set of transforms

patsy-lite accepts a fixed list, for example `log(x)`, `log2(x)`,
`log1p(x)`, `scale(x)`. It computes them itself in pandas, never
through the engine's evaluator, and names the columns predictably
(e.g. `log2__x`). Explainable and safe. It is new syntax to design,
document, test and promise in 1.0.

### Option C: restore the general pass-through

A term that is not a column in the column data goes to formulaic as
written. This brings back the 2017 behaviour, and with it the
code-evaluation, naming and promise concerns above.

## Decision

Option B, chosen by Adam on 2026-11-19 (relayed by the driver session).
The option he picked read: "Support a small whitelist (log, log2, etc.)
in 1.0 and record it in provenance." Transforms are neither removed (A)
nor passed through to the engine (C).

He did not say which transforms are in the set, how a transformed column
is named, how edge cases (zero, negative or missing values, pseudocounts)
behave, or how transforms are recorded in the module JSON and the Process
Run Crate. Those are DETK-0047, Proposed and his, with the planning
session's recommendation. What this record fixes: a fixed, named set;
detk computes the transformed columns itself in pandas, and neither
formulaic nor R ever evaluates an expression from a formula; transforms
are recorded in provenance.

## Consequences

`release/formula-rename` carries out the choice in `docs/formulas.md`
and the module. `release/formula-pin` pins today's behaviour (the term
fails) whichever way this goes. Under A, the new error message is
pinned. Under B or C, the pin changes with the decision and the new
behaviour gets its own tests.

## Replies

- 2026-11-19, adamlabadorf: Planning note: the Consequences above were written before the answer. With Option B, release/formula-rename only removes the np.log claim from docs/formulas.md while renaming; the new node release/formula-transforms implements the set once DETK-0047 settles its details, and changes formula-pin's pin of today's failing term on purpose.
