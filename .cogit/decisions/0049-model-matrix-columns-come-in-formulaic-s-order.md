---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release/formula-pin}
applies: [release/formula-migrate]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: \"I think we should order columns however formulaic orders them, I assume it does it in a conventional way\"; checked: formulaic orders by degree, then as written"}
---

# Model matrix columns come in formulaic's order

- Proposed by: the planning session, 2026-11-19, to record Adam's answer
  to a question the release/formula-pin review (PR #72) raised

## Background

The model matrix's column order is visible to users: it is the order of
the resolved design, of the coefficients in the de results, and it picks
the column DESeq2 reports by default (`--last-term-only` takes the last
one). release/formula-pin pins today's order. For `a*b` it is not the
conventional one. The pin `interaction_star` (`cont ~ binary_str*cat_str`)
gives:

    Intercept, binary_str__control, binary_str__control:cat_str__B,
    binary_str__control:cat_str__C, cat_str__B, cat_str__C

patsy-lite puts patsy's columns back "in formula order" by matching
column names against each term name as a prefix (`patsy_lite.py`, the
`new_order` loop), so each interaction column lands under the first main
effect whose name it starts with. The interactions come before the
second main effect, and this was never designed.

## Context

formulaic (DETK-0024) orders terms by degree, as R's `model.matrix` and
patsy do. Checked with formulaic 1.2.2, `model_matrix` with its default
ordering (`_ordering="degree"`):

| formula | columns |
| --- | --- |
| `y ~ binary_str*cat_str` | `Intercept`, `binary_str[T.control]`, `cat_str[T.B]`, `cat_str[T.C]`, `binary_str[T.control]:cat_str[T.B]`, `binary_str[T.control]:cat_str[T.C]` |
| `y ~ cat_str*binary_str` | `Intercept`, `cat_str[T.B]`, `cat_str[T.C]`, `binary_str[T.control]`, `cat_str[T.B]:binary_str[T.control]`, `cat_str[T.C]:binary_str[T.control]` |
| `y ~ cont:binary_str + cat_str + cont` | `Intercept`, `cat_str[T.B]`, `cat_str[T.C]`, `cont`, `cont:binary_str[T.control]` |
| `y ~ zeta + alpha + cont` | `Intercept`, `zeta`, `alpha`, `cont` |

The intercept comes first, then terms of degree 1, then degree 2 and so
on. Within a degree the terms keep the order written, not alphabetical
order, and the factors of an interaction column keep their written order
too. This is the conventional order.

## Options

### Option A: follow formulaic's order

The port takes formulaic's column order as it is. The `a*b` pins change.

### Option B: reproduce today's order

The port reorders formulaic's columns the way patsy-lite does today.
Keeps the pins, but keeps an order nobody chose.

## Decision

Option A, chosen by Adam on 2026-11-19 (relayed by the driver session):
"I think we should order columns however formulaic orders them, I assume
it does it in a conventional way." The planning session checked that
assumption: formulaic's order is by degree, then as written (Context), as
R and patsy order terms. The column order today's patsy-lite gives is not
part of the 1.0 promise. Column names, the `__` convention and the
values are unchanged by this record.

## Consequences

release/formula-migrate takes formulaic's order. Its PR changes the
`interaction_star`, `interaction_star_refs` and `quote_interaction_star`
pins (and any other pin with an interaction) to that order, and names
them in its description. The CHANGELOG says that in a design with an
interaction, the interaction columns now follow all main effects. So the
last column, which `detk-de deseq2 --last-term-only` reports, is now the
interaction, as in R.
