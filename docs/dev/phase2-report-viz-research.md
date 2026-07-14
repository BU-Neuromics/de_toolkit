# Phase 2 Reporting Redesign — Visualization Research & Decision Record

**Status:** Decision made — Vega-Lite + Python static fallback
**Date:** 2026-07-14
**Method:** Multi-source deep research (21 sources fetched, 89 claims extracted,
25 adversarially verified with 0 refuted). Sources listed at the end.

## 1. Problem

Every detk tool already emits structured per-module JSON (via `DetkModule` /
`DetkReport`). The reporting layer must assemble that JSON into a **single,
self-contained, offline HTML report**. The legacy stack (jQuery 3.3.1,
Bootstrap 4, doT.js, and **Highcharts 6**) is abandoned/half-broken and, in the
case of Highcharts, **commercially licensed** — it cannot be redistributed in an
MIT-licensed project.

### Hard constraints
1. **One self-contained `.html`** that works fully offline (no CDN at view time);
   libraries and data inlined.
2. **Report generation stays pure Python** (Jinja2 templating), pip-installable,
   with **no Node/npm/bundler/JS build step**. Any JS charting library must ship
   as a **pre-built, vendored file** committed to the package.
3. **Permissive license only** (MIT/BSD/Apache/ISC).
4. **Provenance-friendly**: the raw module JSON travels inside the file, and
   charts should be declaratively/inspectably tied to that data.

### Chart types required
Histograms, boxplots, bar charts, scatter (PCA with covariate coloring; volcano
log2FC vs −log10 p; MA), data tables, and threshold/reference lines.

## 2. License screen

Highcharts is **disqualified** — commercial licensing, free for non-commercial
use only. All other candidates are permissive:

| Library | License |
|---|---|
| Plotly.js, Chart.js, uPlot, Recharts, c3 | MIT |
| Apache ECharts | Apache-2.0 |
| Vega, Vega-Lite, vega-embed | BSD-3-Clause |
| D3, Observable Plot | ISC |

(Note: MultiQC *the application* is GPLv3, but that is a property of the app, not
of Plotly.js which it uses — MIT. It does not constrain our choice.)

## 3. Candidate assessment

### Eliminated as primary
- **uPlot** — MIT, ~50 KB single IIFE file, renders 166k points in ~25 ms (the
  performance leader). But it is specialized for time series / lines / areas /
  bars and **does not cover scatter, volcano, PCA, or boxplots** out of the box,
  and its documentation is a single small Markdown file. Disqualified as the
  primary layer; possible future use for dense line/bar charts.
- **Chart.js** — MIT, largest community (~67k stars), but not updated in ~9
  months and weaker for the statistical chart grammar we need.
- **ECharts** — Apache-2.0, broad chart coverage, but ~1 MB bundle and the
  largest open-issue backlog (~1,599) of the candidates.
- **c3** — effectively deprecated (last release 2020).

### Finalists

**Vega-Lite (+ Vega + vega-embed)** — BSD-3-Clause
- A chart is a **single JSON object** combining a data source, a mark type, and
  an encoding mapping — the "chart = spec + data" model. Best-in-class for the
  provenance constraint.
- Data embeds **inline** via the `values` property (arrays of objects — exactly
  detk's per-module JSON shape) or a top-level `datasets` map so multiple charts
  share one embedded dataset. No external URLs required → fully offline.
- Specs are keyed to a **versioned schema**; axes, legends, and scales are
  auto-generated from mark + encoding, reducing hand-written chart code in the
  Python template.
- Ships as vendorable files (Vega, Vega-Lite, vega-embed) usable from plain
  `<script>` tags — **no build step**. Much leaner than Plotly.
- **vega-embed** provides a built-in export menu (PNG/SVG with a `scaleFactor`
  for high-resolution manuscript figures), tooltips, themes, and "View Source" /
  "Open in Vega Editor" actions — reinforcing provenance. Menu items are
  individually toggleable and re-labelable.
- Full grammar covers every required chart type, with threshold/reference lines
  via layering and covariate coloring via encoding channels.
- Weaker spot: dense scatter at genomics scale (10⁴–10⁵ points) is less
  battle-tested/documented than Plotly's WebGL path.

**Plotly.js** — MIT
- Batteries-included; all required chart types native; built-in SVG/PNG export.
- **Best-maintained** of the candidates (v3.7.x, updated within days at time of
  research).
- **WebGL** (`scattergl`) renders ~100k up to ~1M points — attractive for
  volcano/MA/PCA. But: browsers cap **~4–8 WebGL contexts per page** (a real
  limit for a multi-chart report), hover handling **loops over every point**
  (doesn't scale), there is **no viewport downsampling** on zoom, freezing is
  reported around ~180k points, and WebGL **isn't available in every browser** —
  a portability risk for an "opens anywhere" offline file.
- **Heavy**: `include_plotlyjs=True` inlines the full ~3 MB library, producing
  5 MB+ HTML files. Python-side static image export requires the `kaleido`
  dependency.

## 4. Decisive precedent: MultiQC

MultiQC — the dominant bioinformatics reporting tool — is the closest real-world
analog and strongly informs the decision:

- It **migrated Highcharts → Plotly.js in Feb 2024**, motivated largely by the
  **maintenance burden of two codebases** (Highcharts for interactive + matplotlib
  for static images). Plotly let it generate both interactive and static output
  from one Python codebase. (The migration was 200k+ lines and needed workarounds.)
- Its architecture is **exactly our target**: **Jinja2 (pure Python) generation +
  a vendored JS charting library**, producing a self-contained standalone
  `multiqc_report.html`. This proves the pure-Python-generation + vendored-JS
  pattern is production-viable.
- It uses **`kaleido`** for server-side static image export (manuscript figures).
- Critically: at genomics scale, interactive plots **can crash browsers**, so
  MultiQC falls back to **server-side Python-rendered static (“flat”) images**
  embedded in the report. This hybrid is the practical answer to the performance
  constraint.
- Reports can carry the **underlying parsed data** alongside the output
  (TSV/YAML/JSON) — the same provenance philosophy detk already has.
- Added dark mode in Oct 2025.

## 5. detk-specific sizing insight

Most detk charts are **small**, so the genomics-scale performance concern applies
to only a couple of chart types:

| Chart | Approx. data size |
|---|---|
| coldist / rowdist | binned (~20 bins) — tiny |
| colzero / rowzero | ~`n_samples` — tiny |
| entropy | histogram — tiny |
| PCA scatter | ~`n_samples` points — small |
| **volcano / MA** | **per-gene, ~20k–60k points — genomics-scale** |
| enrichment (fgsea) | ~`n_pathways` rows — small |

Only **volcano/MA** (and possibly a raw per-gene rowdist) are large. Everything
else is comfortably interactive in any library.

## 6. Decision

**Primary: Vega-Lite (+ Vega + vega-embed), vendored, with a pure-Python static
fallback (matplotlib SVG) for the large scatter plots (volcano/MA).** SPA glue is
plain vanilla JS (or a tiny no-build layer) that reads the embedded JSON and
mounts one Vega-Lite view per module.

**Rationale.** Vega-Lite aligns best with the project's stated priorities: a lean,
self-contained SPA where the **data travels with the report** and **charts are
declarative JSON specs tied to that data** (uniquely strong provenance and
inspectability), a permissive BSD license, and a bundle a fraction of Plotly's
size. Its one weakness — dense scatter at genomics scale — affects only
volcano/MA, and the MultiQC-proven **Python static fallback** covers exactly that
case while doubling as the manuscript-figure path.

**Runner-up: Plotly.js.** The lower-risk, proven-in-domain choice (MultiQC's), one
library for interactive + static with the least custom work — at the cost of
heavier files, WebGL/portability caveats, and a less provenance-pure model. If
Vega-Lite spec authoring proves too costly in practice, this is the fallback.

### Risks / tradeoffs of the primary choice
- More hand-authored spec templating than Plotly's one-call figures (mitigated by
  Vega-Lite's auto axes/legends/scales and reusable per-module spec builders).
- A second rendering path (Python static) to maintain for large scatters — but
  that path is required for manuscript figures regardless, and MultiQC validates
  the hybrid.
- Three vendored JS files (Vega, Vega-Lite, vega-embed) instead of one — still
  no build step, still far smaller inlined than Plotly.

## 7. Proposed architecture

- **Generation (pure Python):** `detk-report` collects module JSON (unchanged),
  and a Jinja2 template inlines: (a) the vendored Vega/Vega-Lite/vega-embed JS,
  (b) the raw module JSON as an embedded `<script type="application/json">`
  block, (c) a small vanilla-JS controller, (d) per-module Vega-Lite spec
  builders (JSON with inline/dataset-referenced data).
- **Rendering (client, no build):** the controller reads the embedded JSON and
  calls `vegaEmbed(...)` per module; vega-embed supplies interactivity + PNG/SVG
  export + spec inspection.
- **Static fallback (pure Python):** for volcano/MA (and any oversized plot), and
  for manuscript figures, render matplotlib SVG server-side and embed inline;
  optionally offer both a static image and an interactive view.
- **Schema work (prerequisite):** standardize the module JSON `properties`/`params`
  schema first (fix the empty-`params` modules and key drift noted in the Phase 1
  memo) so each Vega-Lite spec builder maps cleanly to a stable data contract.

## 8. Sources

Primary/spec:
- Vega usage — https://vega.github.io/vega/usage/
- Vega-Lite data / inline `values` / `datasets` — https://vega.github.io/vega-lite/docs/data.html
- Vega-Lite spec structure — https://vega.github.io/vega-lite/docs/spec.html
- Vega-Lite embed guide — https://vega.github.io/vega-lite/usage/embed.html
- vega-embed (export, BSD-3, offline vendoring) — https://github.com/vega/vega-embed
- Configuring vega-embed export menu — https://dev.to/joaompalmeiro/how-to-configure-vega-embed-for-a-single-altair-chart-4chd
- Plotly `write_html` / `include_plotlyjs` — https://plotly.github.io/plotly.py-docs/generated/plotly.io.write_html.html
- Plotly interactive HTML export — https://plotly.com/python/interactive-html-export/
- Plotly performance / WebGL — https://plotly.com/python/performance/ , https://plotly.com/javascript/webgl-vs-svg/
- uPlot — https://github.com/leeoniya/uPlot

Precedent (MultiQC):
- MultiQC + Plotly migration — https://seqera.io/blog/multiqc-plotly/
- MultiQC 10-year retrospective — https://seqera.io/blog/multiqc-turns-10/
- MultiQC repo — https://github.com/multiqc/multiqc
- MultiQC reports (static fallback, SVG export) — https://docs.seqera.io/multiqc/reports/

Comparative / maintenance / performance:
- npm-compare (licenses, footprints) — https://npm-compare.com/c3,chart.js,d3,echarts,highcharts,plotly.js,recharts,vega,vega-lite
- npmtrends — https://npmtrends.com/chart.js-vs-echarts-vs-plotly.js-vs-vega-lite
- Plotly scattergl large-data forum — https://community.plotly.com/t/performance-issues-with-scattergl-plotly-js-v2-35-3-for-large-datasets/90455
- Plotly.js SVG scale limits — https://github.com/plotly/plotly.js/issues/5641
- uPlot review — https://cprimozic.net/notes/posts/my-thoughts-on-the-uplot-charting-library/
