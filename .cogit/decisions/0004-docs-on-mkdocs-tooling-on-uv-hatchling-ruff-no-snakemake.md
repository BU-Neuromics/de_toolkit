---
template: adr
state: Accepted
authority: [human]
date: 2026-08-11
from: {node: modernize/phase3}
applies: [modernize]
revisions:
  - {date: 2026-08-11, by: adamlabadorf, change: Accepted, why: "merged PR #30, which carried the decision document"}
---

# Docs on MkDocs, tooling on uv, hatchling and ruff, no Snakemake

- Proposed by: a coding session, Phase 3 (2026-08-11)
- Reconstructed 2026-11-09 (COG-0130, option A); the full record is
  `docs/dev/phase3-infra-decisions.md`

## Background

Three infrastructure choices made together in Phase 3 because they
interact: the documentation system, the packaging and tooling stack,
and Snakemake's place in the repository.

## Decision

1. Documentation moves from Sphinx on ReadTheDocs to MkDocs Material,
   built and deployed to GitHub Pages by GitHub Actions.
2. uv manages the project, hatchling builds it, ruff lints and
   formats it; not Poetry.
3. Snakemake is dropped as internal machinery; detk stays pure Python,
   and workflow managers are documented as integration targets.

## Consequences

The ReadTheDocs build (#14) and the Snakemake end-to-end test (#12)
are retired; the docs build is a strict CI gate. See the document for
the reasons behind each choice.
