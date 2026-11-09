---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/agent-skills, step: s1}
applies: [release/agent-skills]
allowed_by: [reasonable]
reason: skill command lines and copied usage blocks are checked against the installed CLI in CI, so drift fails a build rather than misleading an agent
---

# Keep the agent skill in step with the CLI through a test against --help

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
