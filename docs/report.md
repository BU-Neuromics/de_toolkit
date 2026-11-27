# Reports

detk's reporting layer gives every analysis two artifacts for free:

1. **Machine-readable provenance** — every tool invocation records a JSON
   document capturing what was run, with what parameters, and what it found.
2. **A human-readable report** — a *single, self-contained* HTML file
   rendering all recorded results as interactive charts. No network access,
   no external files; you can email it, archive it, or attach it to a paper.

**See one now:** a [live example report](example/detk_report.html) generated
from the public airway RNA-seq dataset by the [worked example](example.md).

## How it works

Unless `--no-report` is passed, each detk tool serializes a JSON document into
`<report-dir>/json/` (default `./detk_report/json/`) as a side effect of the
run. Documents are named by a content hash of what identifies a run (see
[What identifies a record](#what-identifies-a-record)), so re-running the same
command updates its document in place rather than accumulating duplicates,
while runs with different parameters or different files coexist.

Run tools, then render:

```bash
detk-stats summary raw_counts.csv sample_info.csv -o raw_stats.csv
detk-filter "nonzero(all) > 0.5" -o filtered.csv raw_counts.csv
detk-norm deseq2 -o norm.csv filtered.csv

detk-report generate
```

This produces `detk_report/detk_report.html` containing a view for every
recorded module, organized by family (stats, filter, norm, ...) in a
collapsible navigation tray.

```text
usage: detk-report generate [options]

options:
  -h, --help  Print this help and exit
  --dev       Pretty-print the embedded JSON payload (larger file, easier to
              read)
```

`detk-report generate` reads the report directory given with
`--report-dir` (default `./detk_report`), one of the
[common options](tools/index.md#common-options).

`detk-report clean` deletes the report directory, with its accumulated JSON,
the HTML report and the provenance crate in it.

```text
usage: detk-report clean [options]

options:
  -h, --help  Print this help and exit
```

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
its report-relevant `properties`, the detk version, timing, the process
argument vector, and input/output file paths. The document format is versioned
(`schema_version`) and specified by a JSON Schema shipped inside the package
(`de_toolkit/module_schema.json`); every emitted document is validated against
it in detk's test suite. For example (abbreviated):

```json
{
  "name": "colzero",
  "detk_version": "1.0.0",
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

### What identifies a record

A document's `id`, and so its file name `json/<id>.json`, is a hash of:

- the module `name` and its `params`
- every input and output path, as recorded (relative to `workdir`):
  `in_file_path`, `out_file_path`, `column_data_path` and, when present,
  `in_file_paths` and `out_file_paths`
- the recorded command line, `argv`
- the detk version

Two runs that differ in any of these keep two records: `detk-filter` run
with `-o a.csv` and then `-o b.csv`, `detk-de deseq2` run on two sample
information files, or `detk-enrich fgsea` run on two results files (fgsea
records its GMT as `in_file_path`; the results file is in its `argv`). A run
identical in all of them, the same command from the same directory, writes
the same `id` and replaces its one record. Because paths and the command
line are hashed as recorded, an absolute path and its relative spelling give
the same `id`; a command spelled differently (`-o` for `--output`, or an
extra `-v`) gives a new one. Ids change with each detk version.

### Document schema

The envelope is versioned (`schema_version`, currently **1.2**) and specified
by a JSON Schema shipped inside the package at `de_toolkit/module_schema.json`
([view on GitHub](https://github.com/BU-Neuromics/de_toolkit/blob/main/de_toolkit/module_schema.json)).
Required fields:

| Field | Type | Meaning |
|-------|------|---------|
| `name` | string | module name (lowercased `DetkModule` subclass) |
| `id` | string | content hash of what identifies the run (name, params, every input and output path, command line, detk version); see [What identifies a record](#what-identifies-a-record) |
| `schema_version` | string | version of this envelope format |
| `detk_version` | string | de_toolkit version that wrote the document |
| `last_modified` | integer | unix ms timestamp of the write |
| `params` | object | invocation parameters (empty only for modules that take none) |
| `properties` | object | module-specific results consumed by the report views |

Optional fields:

| Field | Type | Meaning |
|---|---|---|
| `start_time` / `end_time` | string | ISO 8601 UTC |
| `argv` | array | the command line; `argv[0]` is the command's name only (`detk-stats`); the other arguments as typed, except that an absolute path, alone or as an option's value (`--report-dir=/abs/rep`, `-o/abs/out.csv`), is written **relative to `workdir`**, so the line re-runs the same from there |
| `workdir` | string | the directory the command ran in, **relative to the report directory**: `..` for the default `./detk_report` |
| `in_file_path`, `out_file_path`, `column_data_path` | string | the input, output and column data files, **relative to `workdir`** (a path typed as absolute is written relative too) |
| `in_file_paths`, `out_file_paths` | array | since 1.1: every input and output file of a step with several, written by [`detk-util record`](tools/util.md#record), each relative to `workdir`; their first entries are also `in_file_path` and `out_file_path` |

So a file's location is the report directory, then `workdir`, then the
path: `detk_report/../counts.csv`. No recorded path is absolute, whether you
typed paths relative or absolute: `argv` and the parameters and checksums of
[`detk-util record`](tools/util.md#record) are written relative to `workdir`
too (DETK-0281), so a report directory can be moved or published as it is.
What that leaves out:

- **An argument that is not a path.** detk rewrites an argument that is an
  absolute path (or an option's value that is one), not paths inside an
  argument. An argument counts as a path when it is an absolute path that
  exists, whitespace or not (`/home/me/proj/My Data/c.csv` is written
  `My Data/c.csv`, DETK-0590); one that does not exist counts only when it
  starts with `/`, has no whitespace and its parent directory exists
  (DETK-0580), as an output not yet written does. Any other argument is
  written as typed, even one that starts with `/`: an awk
  program (`'/^gene/ {print}'`), a regular expression (`'/^g1,/'`) or a
  shell script (`sh -c "/usr/bin/env echo hi"`). An absolute path to a
  file in a directory that does not exist is kept as typed too. The script
  of `sh -c` is one argument, so it is written as typed, absolute paths and
  all. Run in `/home/me/proj`,

    ```console
    $ detk-util record -i /home/me/proj/a.csv -o /home/me/proj/b.csv -- sh -c "cp /home/me/proj/a.csv /home/me/proj/b.csv"
    ```

    records

    ```json
    {
      "argv": ["detk-util", "record", "-i", "a.csv", "-o", "b.csv", "--",
               "sh", "-c", "cp /home/me/proj/a.csv /home/me/proj/b.csv"],
      "in_file_paths": ["a.csv"],
      "out_file_paths": ["b.csv"]
    }
    ```

    so write such steps with relative paths (`sh -c "cp a.csv b.csv"`).
- **The program of a recorded step.** Typed as an absolute path, it is
  written by its name when `PATH` finds that same file by that name
  (DETK-0390): `detk-util record ... -- /usr/bin/cp a.csv b.csv` records
  `cp a.csv b.csv`, as a detk command's `argv[0]` is its name. A program
  `PATH` does not find, or finds as another file, is written relative like
  any other path. So on a system where `/bin` and `/usr/bin` are separate
  directories, `/bin/cp` is recorded as a relative path
  (`../../../bin/cp` from `/home/me/proj`) when `PATH` finds `/usr/bin/cp`
  first; where `/bin` is a link to `/usr/bin`, as on most current Linux
  systems, it is the same file and is written `cp`. Type the program by its
  name to record it by its name.
- **The directories a relative path climbs through.** With the report
  directory, or a file, in another tree from the working directory, the
  `../` chain spells that tree's directories: `--report-dir /tmp/rep` run in
  `/home/me/proj` records `workdir` as `../../home/me/proj`. That is the
  only form of `workdir` that keeps the location rule above, so detk keeps
  it; keep the report directory and the data under the working directory to
  avoid it.

Since 1.2; documents of 1.0 and 1.1 hold `workdir` and `argv[0]`
absolute, and an absolute `workdir` joined to the report directory is itself,
so the same rule reads them.

The version is `major.minor`: the minor version goes up for an addition every
older document still satisfies, or a change of what a field holds that the
same rule still reads in older documents (1.1 added the two optional lists;
1.2 made the paths relative), the major version for a change that is not. Every document detk emits is validated against the schema in the
test suite; validate your own consumers against the same file. Small
p-values never appear as raw floats in `properties` — the encoder rounds
floats to 3 decimals, so modules emit `-log10` values or preformatted strings
instead.

These documents are the intended integration point for any downstream tooling
that wants to consume detk results programmatically — LIMS systems, QC
dashboards, meta-analyses. The same JSON is also embedded verbatim inside the
generated HTML, so a report file is self-certifying: the data behind every
chart travels with it.

## Standards-based provenance: the Process Run Crate

Alongside the report, in the report directory, detk writes an
`ro-crate-metadata.json`, describing every recorded invocation in community-standard
terms: the [Process Run Crate] profile of [Workflow Run RO-Crate], built on
[RO-Crate]. This is a second, standards-facing view of the same facts as the
module JSON:

- each detk invocation is a `CreateAction`, with start/end times
- each subtool (e.g. `detk-norm deseq2`) is a `SoftwareApplication` with its
  version
- invocation parameters are `PropertyValue` entities
- input and output files are shared `File` entities, so the chaining of tools
  through files — the *implicit workflow* — is visible in the metadata graph
- standard output is not listed as a file: a command that wrote its result
  to stdout (`out_file_path` `stdout`, the `-o` default) has no `File` for
  it. A file really named `stdout` is recorded `./stdout` and listed
- a step recorded by [`detk-util record`](tools/util.md#record) is a
  `CreateAction` whose instrument is the external tool, with its version,
  and lists every file it was given with `-i` and `-o`
- only the files `detk-util record` checksummed carry `sha256` and
  `contentSize`: the inputs and outputs of a step it recorded. The files of
  detk commands carry neither, unless a recorded step also read or wrote
  the same file

The crate is rooted in the report directory, so each report directory has
its own crate: two analyses run in one directory with different
`--report-dir` values never overwrite each other's provenance. Every file is
named by its path relative to the report directory (`../counts.csv` for a
file in the working directory of the default `./detk_report`), never by an
absolute path or `file://` URI, so the report directory is a self-describing
research object wherever it is copied, as long as the files beside it come
too. Standard RO-Crate tooling
(`rocrate-validator`, `runcrate report`, WorkflowHub, Zenodo RO-Crate
deposits) can inspect it without detk installed, and the crate maps to W3C
PROV-O via the profile's published mapping. detk validates its emitted crates
against the Process Run Crate profile in its test suite.

The crate is derived entirely from the module JSON under
`<report-dir>/json/`, is rewritten on every report generation, and is removed
with the report directory by `detk-report clean`. (detk before 1.0 wrote it to
the working directory; `clean` leaves such a `./ro-crate-metadata.json`
alone.) detk does not assert a license over your data — the
crate's `license` field says so explicitly; replace it with your license when
publishing.

**Archiving:** if you publish the analysis directory to Zenodo/OSF (e.g. with
a sync tool such as [datapin]), the report directory in the deposit *is* a
valid RO-Crate whose references reach the data beside it, so the archived
object remains machine-readable provenance, not just a pile of CSVs.

[Process Run Crate]: https://www.researchobject.org/workflow-run-crate/profiles/process_run_crate/
[Workflow Run RO-Crate]: https://www.researchobject.org/workflow-run-crate/
[RO-Crate]: https://www.researchobject.org/ro-crate/
[datapin]: https://github.com/BU-Neuromics/datapin

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
