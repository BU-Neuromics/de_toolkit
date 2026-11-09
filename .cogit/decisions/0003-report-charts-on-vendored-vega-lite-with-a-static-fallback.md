---
template: adr
state: Accepted
authority: [human]
date: 2026-07-14
from: {node: reporting/stats}
applies: [reporting]
revisions:
  - {date: 2026-07-14, by: adamlabadorf, change: Accepted, why: "merged PR #3, which carried the decision document"}
---

# Report charts on vendored Vega-Lite, with a static fallback

- Proposed by: a coding session, Phase 2 (2026-07-14)
- Reconstructed 2026-11-09 (COG-0130, option A); the full record, with
  its research and sources, is `docs/dev/phase2-report-viz-research.md`

## Background

`detk-report` writes a self-contained HTML report from each module's
JSON output. Its old frontend used Highcharts, whose licence conflicted
with detk's MIT licence.

## Decision

The report is a single-file page that mounts one Vega-Lite view per
module from the embedded JSON, with Vega, Vega-Lite and vega-embed
vendored, and a matplotlib SVG fallback for the genomics-scale
scatter plots (volcano, MA). Plotly.js is the fallback choice if
Vega-Lite specs prove too costly to write.

## Consequences

The data travels with the report and every chart is a declarative
spec tied to it; the static path doubles as the manuscript-figure
path. See the document for risks and the proposed architecture.
