---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/fgsea-statcol, step: s2}
applies: [release-1-0-1/fgsea-statcol]
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A. Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27"}
---

# The airway tutorial's fgsea -c sentence after DETK-0600

- Proposed by: the @reviewer session of release-1-0-1/fgsea-statcol s2, 2026-11-27

## Background

After release-1-0-1/fgsea-statcol (PR #190), `detk-enrich fgsea` without
`-c` exits 2 when more than one numeric column besides the ID column could
rank (DETK-0600). docs/tutorials/airway.md lines 352-354 still say "without
it detk would rank by the last numeric column, the treatment's adjusted
p-value, which ranks by the wrong quantity and in the wrong direction".
That is the 1.0.0 behaviour; on 1.0.1 it is false (detk exits 2 naming the
candidate columns). The tutorial's command itself passes `-c` and still
works.

## Context

- The fgsea-statcol node's scope does not include docs/tutorials/airway.md,
  and no other release-1-0-1 node's scope does: skill-guidance covers
  skills/detk/ (where SKILL.md line 272 says the same thing and is already
  planned to change), docs/agent-skills.md and docs/tutorials/quantifiers.md;
  quickstart-deseq2 covers the quickstart.
- The reviewer changes nothing; a scope change is a plan decision.
- Criteria: 1.0.1 ships with no doc that describes the old behaviour as
  current; the smallest change to the plan.

## Options

**A. Add +docs/tutorials/airway.md to fgsea-statcol's scope and fix the
sentence in PR #190** (recommended). The sentence describes exactly the
behaviour this node changes; it is a two-line edit the developer can make
before merge, and the CHANGELOG entry already covers it.

**B. Add +docs/tutorials/airway.md to skill-guidance's scope.** That node
already follows fgsea-statcol and rewrites the same guidance in SKILL.md;
but its subject is the agent skill, not the docs site's tutorials.

**C. Leave it.** 1.0.1's docs would contradict its behaviour; rejected
against the first criterion.

## Decision

A: the fix belongs with the change that made the sentence wrong.

## Consequences

The fgsea-statcol node's scope gains +docs/tutorials/airway.md and PR #190
gets one more commit before merge. If B is chosen instead, skill-guidance's
scope and acceptance gain the tutorial line. Either way, a repository-wide
grep for "last numeric column" outside CHANGELOG and tests should come back
empty before the 1.0.1 cut.
