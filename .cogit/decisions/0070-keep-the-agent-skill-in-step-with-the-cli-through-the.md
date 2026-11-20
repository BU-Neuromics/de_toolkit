---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-20
from: {node: release/cli-migrate, step: s3}
applies: [release/cli-migrate]
allowed_by: [reasonable]
reason: "DETK-0010's mechanism moves from docopt to argparse with the parser it checks against (DETK-0023); the decision itself is unchanged"
---

# Keep the agent skill in step with the CLI through the argparse parsers

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
