# Reports

detk's reporting layer gives every analysis two artifacts for free:

1. **Machine-readable provenance** — every tool invocation records a JSON
   document capturing what was run, with what parameters, and what it found.
2. **A human-readable report** — a *single, self-contained* HTML file
   rendering all recorded results as interactive charts. No network access,
   no external files; you can email it, archive it, or attach it to a paper.

## How it works

Unless `--no-report` is passed, each detk tool serializes a JSON document into
`<report-dir>/json/` (default `./detk_report/json/`) as a side effect of the
run. Documents are named by a content hash, so re-running the same command
with the same parameters updates its document in place rather than
accumulating duplicates, while runs with different parameters coexist.

Run tools, then render:

```bash
detk-stats summary raw_counts.csv sample_info.csv -o raw_stats.csv
detk-filter "nonzero(all) < 0.5" -o filtered.csv raw_counts.csv
detk-norm deseq2 -o norm.csv filtered.csv

detk-report generate
```

This produces `detk_report/detk_report.html` containing a view for every
recorded module, organized by family (stats, filter, norm, ...) in a
collapsible navigation tray.

```text
Usage:
    detk-report generate [options]
    detk-report clean [options]

Options:
    --dev                Pretty-print the embedded JSON payload (larger file,
                         easier to read)
    --report-dir=DIR     Specify the report directory [default: ./detk_report]
```

`detk-report clean` deletes the report directory and its accumulated JSON.

## The report

- Charts are rendered with [Vega-Lite] (vendored into the HTML — the report
  works offline forever).
- Light/dark theme toggle, persisted across visits.
- Every chart offers **SVG/PNG export** for figures, and a **"Show data"**
  toggle revealing the exact JSON the chart was built from — the report never
  shows you a picture you can't trace back to data.
- Modules without a dedicated chart yet render their raw JSON rather than
  being dropped.

[Vega-Lite]: https://vega.github.io/vega-lite/

## The module JSON documents

Each document contains the module's `name`, the `params` it was invoked with,
its report-relevant `properties`, the detk version, and input/output file
paths. For example (abbreviated):

```json
{
  "name": "colzero",
  "detk_version": "0.9.12",
  "params": {},
  "properties": {
    "zeros": [
      {"name": "sample_1", "zero_count": 4102, "zero_frac": 0.15, "...": "..."}
    ]
  },
  "in_file_path": "raw_counts.csv",
  "out_file_path": "raw_stats.csv"
}
```

These documents are the intended integration point for any downstream tooling
that wants to consume detk results programmatically — LIMS systems, QC
dashboards, meta-analyses. The same JSON is also embedded verbatim inside the
generated HTML, so a report file is self-certifying: the data behind every
chart travels with it.

## Using reports in a workflow

Report JSON accumulates in the working directory (or wherever `--report-dir`
points), so the natural pattern in a workflow manager is to make
`detk-report generate` a final step that depends on all detk-invoking steps —
see the [Quickstart](quickstart.md#using-a-workflow-manager) for a complete
Snakemake example.

## Library usage

From Python, modules emit their JSON through a context manager:

```python
from de_toolkit.report import DetkReport
from de_toolkit.stats import BaseStats
from de_toolkit.common import CountMatrixFile

with open("counts.csv") as f:
    counts = CountMatrixFile(f)

with DetkReport("my_report_dir") as r:
    r.add_module(
        BaseStats(counts),
        in_file_path="counts.csv",
        workdir=".",
    )
# my_report_dir/detk_report.html is written on context exit
```
