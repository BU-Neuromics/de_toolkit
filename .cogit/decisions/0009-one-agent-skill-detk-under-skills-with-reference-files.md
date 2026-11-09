---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/agent-skills, step: s1}
applies: [release/agent-skills]
allowed_by: [reasonable]
reason: "npx skills reads skills/<name>/SKILL.md; one skill with references loads on any detk request and keeps install and flow together"
---

# One agent skill, detk, under skills/ with reference files

## Background

<!-- What a reader who has not seen the codebase, or has been away for a month, needs to know to read this record: the thing it concerns, in plain words, and why it matters. No decision here. -->

## Context

<!-- What forces are at play: the problem, the constraints, and the criteria the decision is judged against. -->

## Options

<!-- At least two real options, each scored against the criteria. -->

## Decision

<!-- The option chosen and the one or two reasons that decided it. -->

## Consequences

<!-- What becomes easier or harder, the follow-up work, and what would make us revisit. -->
