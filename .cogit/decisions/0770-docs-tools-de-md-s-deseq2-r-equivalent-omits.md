---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/quickstart-deseq2, step: s2}
applies: [release-1-0-1/quickstart-deseq2]
issue: 197
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Option 1: widen release-1-0-1/quickstart-deseq2's scope to +docs/tools/de.md and fix the R block in #188, rather than plan a follow-up node; matches DETK-0760's handling. Accepted on Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27."}
---

# docs/tools/de.md's DESeq2 R equivalent omits independentFiltering=FALSE

## Background

PR #188 (release-1-0-1/quickstart-deseq2, #184) adds a paragraph by the
quickstart's `detk-de deseq2` example: detk's `padj` is BH over every gene,
with no independent filtering and no Cook's distance cutoff, and "the
`detk-de deseq2` page states the `results()` settings this matches". That
page, docs/tools/de.md, says in prose "no independent filtering is
performed", but its "roughly equivalent" R block ends with
`write.csv(results(dds, cooksCutoff=Inf), de.out.fn)`. `results()` defaults
to `independentFiltering=TRUE`, so the R a reader copies from the page the
quickstart now sends them to still applies independent filtering and gives a
different `padj` (NA for low-count genes, a different BH denominator) from
detk's. The code (de_toolkit/de.py, `nbinomWaldTest` then
`p.adjust(..., method='fdr')` per coefficient) does no independent filtering.

## Context

- The quickstart paragraph itself is accurate; the defect is in de.md, which
  is outside this node's scope (docs/quickstart.md, tests/docs/, +CHANGELOG).
- The node's acceptance asks that de.md "states the matched results()
  settings"; its prose does, its code block does not.
- 1.0.1 is a docs-accuracy patch release; the fix is one argument.

## Options

1. Widen this node's scope to docs/tools/de.md and have the developer change
   the block to `results(dds, independentFiltering=FALSE, cooksCutoff=Inf)`,
   with a tests/docs assertion. Closes the gap in the same PR; one more
   round-trip on #188.
2. Accept #188 as is and plan a follow-up node under release-1-0-1 for the
   de.md R block (and the test). Keeps this node's scope; the quickstart
   points at an inaccurate snippet until the follow-up lands, but both ship
   in 1.0.1.
3. Leave it. The page's prose is right; the block is labelled "roughly".

## Decision

Recommended: option 2, a follow-up node in release-1-0-1 that changes the R
block to `results(dds, independentFiltering=FALSE, cooksCutoff=Inf)` and adds
a tests/docs check, so 1.0.1 ships both without reopening a reviewed PR.
Option 1 is equally fine if Adam prefers one PR. Not option 3: the new
quickstart text sends readers to that block specifically for the settings.

## Consequences

A follow-up node to plan (or a scope change on this one). Revisit if de.md's
"roughly equivalent" block is rewritten wholesale.

## Replies

- 2026-11-27, adamlabadorf: The option accepted is option 1, not the Decision section's recommended option 2: release-1-0-1/quickstart-deseq2's scope was widened to docs/tools/de.md and the R block fixed in PR #188 (095e424, scope entry made bare in 5eafd7a), with no follow-up node, matching DETK-0760's handling.
