---
template: analysis
state: Proposed
authority: [human]
date: 2026-11-20
from: {node: release}
applies: [release]
---

# Survey of CSV command-line tools for deriving covariates

- Proposed by: the planning session, 2026-11-20, to keep the research
  report behind Adam's answer to DETK-0051 in the record
- Research by: a research session for the driver, 2026-11-20 (the
  report is kept below as written, with its headings moved down one
  level; nothing in the repository was changed by that research)

## Background

DETK-0050 keeps design formulas to the model alone, so derived
covariates (a constant column, logs, z-scores, min-max scaling) have to
be added to the column data file before a detk step reads it.
DETK-0051 drafted a detk command for that, `detk-augment`. Before
answering, Adam asked whether detk should build it at all, or whether
an existing tool already does this well. This record is that research;
DETK-0051 records his answer.

## Question

Should detk build `detk-augment` (a), build a separate tidyr-style
utility package (b), or document an existing command-line tool and
build nothing (c)? If (c), which tool, and how does the step stay in
detk's provenance?

## Evidence examined

Each tool was installed in a throwaway conda environment (conda-forge
unless noted) and run on the same sample sheet:

- Miller (`mlr`) 6.22
- xan 0.61
- qsv 14.0 (conda-forge; upstream is at 29.0)
- DuckDB CLI 2.0
- csvtk 0.39, csvkit 2.2, GNU datamash 1.9
- Checked as abandoned or stale, not run: xsv, tsv-utils, polars-cli,
  q, csvq, dplyr-cli
- Tool documentation where a behaviour was not obvious from a run
  (Miller's `docs/src/two-pass-algorithms.md`; DuckDB's CSV reader)

## Method

A small sample sheet with zero-padded IDs (`007`, `010`, `0012`), an ID
that looks like a number (`1e5`), a 0 in `age`, and a missing value in
`rin`. Each tool was asked for DETK-0051's operations (a constant
column, log with a base and a pseudocount, z-score with n-1, centring,
min-max) and checked for: IDs kept as written (DETK-0015), the standard
deviation's denominator, and what happens on a zero and on a missing
value.

## Finding

### Should detk build `detk-augment`? A survey of CSV command-line tools

**My recommendation is (c) with a small addition.** Document one existing tool in detk's docs and skill, with tested recipes for the operations in DETK-0051; Miller is my first choice. Then add one small detk command that records an external step in detk's provenance. I don't recommend (b), a separate package. If structured provenance and safe defaults matter more to you than not reinventing, (a) as drafted is still a sound fallback. This is research only: nothing in the repo, its dependencies or the cogit record was changed.

#### What I tested

I ran each tool on a small sample sheet in a throwaway conda env in the scratchpad, plus qsv 14 that was already installed. The sheet had zero-padded IDs (`007`, `010`, `0012`), an ID that looks like a number (`1e5`), a 0 in `age`, and a missing value in `rin`.

#### The serious candidates

**Miller (`mlr` 6.22)** is the strongest overall.
- **Status:** active, last release 2026-09, BSD-2-Clause. Installs from conda-forge `miller`, Homebrew, or as a single static Go binary.
- **Operations:**
  - Constant column: `mlr --csv put '$batch="b1"'`
  - Log with a pseudocount: `put '$age_log2_pc1 = log($age+1)/log(2)'`. There is no base argument.
  - Z-score: two passes in one command: `put -q '@r[NR]=$*; @a[NR]=$age; end{m=mean(@a); s=stddev(@a); for(k,v in @r){v["age_zscore"]=(v["age"]-m)/s; emit v}}'`
  - `stddev` uses n-1. Its docs give min-max as their two-pass example (docs/src/two-pass-algorithms.md).
- **Other verbs:** `cut`, `rename`, `filter`, `reshape` (long↔wide), `join`.
- **IDs:** `007`, `0012` and `1e5` all came back as written; leading zeros only turn numeric with `-O`.
- **Gotchas:** `log10(0)` writes `-Inf` silently, and a missing value gives an empty result silently.

**xan (0.61)** has the nicest syntax.
- **Status:** active, last release 2026-09, Unlicense. Installs from conda-forge or Homebrew.
- **Operations:**
  - Log with a base: `xan map 'log(age+1, 2) as age_log2_pc1, "b1" as batch'`
  - Z-score and min-max: `xan window 'mean(age) as m, stddev_sample(age) as s, …' | xan map '(age-m)/s as age_zscore'`
- **Verbs:** a complete set (`select`, `rename`, `filter`, `pivot`, `unpivot`, `join`, `agg`).
- **IDs:** kept as written.
- **On the plus side:** a missing value is a hard error.
- **Gotchas:**
  - Plain `stddev` divides by n (the population formula), not n-1.
  - `log(0)` gives `-inf`.
  - It is still 0.x, so its syntax may change.
  - Coding agents have seen much less of it than Miller.

**qsv (upstream 29.0; conda-forge only has 14.0, built with all features)**
- **Operations:** `luau map` (Lua) works and keeps IDs. `sqlp` (Polars SQL) does everything in one query.
- **Gotchas:**
  - `sqlp` turned `007,010,0012` into `7,10,12`, which breaks DETK-0015.
  - `sqlp` did integer division on min-max (34/61 gave 0).
  - `qsv stats` uses the population SD.
- Too many sharp edges to point users at.

**DuckDB CLI (2.0)**
- **Status:** active, MIT.
- **Operations:** a z-score with window functions in one query. `stddev` uses n-1.
- **IDs:** its CSV reader kept `007` as text in my test, but the docs don't promise this. Pin types or use `all_varchar=true`.
- **Gotcha:** `log()` is base 10 (`ln` is natural log).
- Powerful, but SQL is a heavier ask than a verb.

**Weaker or not usable:**

| Tool | Problem |
|---|---|
| csvtk (0.39) | Good tidyr verbs (`gather`/`spread`/`join`/`rename`), but **no log function** in either expression language (I tested both). It rounds results to 2 decimals by default and needs `-s` to keep IDs. |
| csvkit (2.2) | Turns `007` into 7 by default. No mutate verb except via SQL, and its `csvsql` crashed against the SQLAlchemy 2.1 that a fresh conda install pulls in. |
| GNU datamash (1.9) | Good statistics (`sstdev`/`pstdev` explicit), but no expressions, no log, no join. |
| Abandoned | xsv (archived; its README points to qsv or xan), tsv-utils (no commits since 2021), polars-cli (archived), q and csvq (stale since 2021 and 2023), dplyr-cli (stale since 2022). |

I found no maintained CLI for tidyr or dplyr. Anything like that would mean `Rscript -e` with tidyverse.

**Conda channels:** bioconda's own builds of csvtk (0.31) and datamash (1.1.0, from 2016) are out of date; use conda-forge.

**What every tool shares:** none of them gives DETK-0051's safety defaults out of the box (an error on zero after the pseudocount, an error naming samples with missing values, n-1 every time). A recipe has to add those checks, or users get them wrong. The difference in z-scores between n-1 and n is a factor of √(n/(n−1)), about 15% at n=4, and it would go unnoticed in a design matrix.

#### The three directions

**(a) `detk-augment` inside detk, as drafted**
- **Provenance:** complete. Structured `params`, and the means, SDs and minimum/maximum that were used land in `properties`, so a column can be reproduced and applied to new samples.
- **Defaults:** safe, and they match `plog`.
- **Size:** small to build, maybe a few hundred lines plus tests and docs.
- **Cost:** three new subcommands promised until 2.0, and it reinvents a narrow slice of what Miller and xan do.

**(b) A separate tidyr-style utility package**
- **Scope:** the most work. To be worth reusing it needs the whole verb set, and Miller and xan already are that, mature and maintained.
- **Provenance:** the hardest of the three. It would need its own provenance format, or would have to write detk's module JSON (so it isn't really independent), and detk's crate would have to read its output.
- **1.0 promise:** detk's own surface stays the same, but you now maintain a second package.
- I'd only consider it if you want a general lab tool for its own sake.

**(c) Document an existing tool and build nothing**
- **Scope and 1.0:** nothing new to promise; detk's docs and agent skill carry tested Miller recipes, with checks for zero and missing values written into them.
- **Provenance:** a step outside detk doesn't appear in the module JSON or crate. A `detk-de` run would show an untracked input with no step that produced it.
- **Closing the gap generically:** a small wrapper such as `detk-util record --in sample_info.csv --out aug.csv -- mlr --csv put '…' sample_info.csv`.
  - It runs the command and writes a module JSON with the command line, the tool name and `--version`, and file paths.
  - That fits the current schema (name, id, params, properties) plus a `SUBTOOLS` entry.
  - The crate would then show the step as a `CreateAction` whose instrument is Miller, with the command as a `PropertyValue`.
  - Inputs and outputs have to be named explicitly, because the wrapper can't parse arbitrary commands.
  - It also covers any other external step (awk, an R script).
  - What it records is the command, not structured statistics, and detk can't vouch for the safety checks.
- **Dependency:** Miller doesn't have to become a detk dependency; it's on conda-forge, which bioconda already builds on.

**Why I lean to (c) with `record`:**
- It takes your "don't reinvent" point seriously.
- The one thing detk must own, provenance, is covered generically and only once.
- It adds one subcommand to 1.0 instead of three.

The cost is that the safe defaults move from code into documented recipes, so they are only as good as the docs and skill. Choose (a) if structured, checked provenance for derived covariates is worth that.

#### Overlap with `detk-util`

A tidyr verb set would overlap detk-util, but these commands carry checks a generic verb wouldn't:

| detk-util | dplyr/tidyr equivalent | What detk adds |
|---|---|---|
| `tidy-covs` | a `semi_join` plus reordering rows to match the counts columns | fails when a sample is missing |
| `tidy-counts` | `select` of the counts columns in column data order | fails when a sample is missing |
| `annotate` | `left_join` plus `summarise(paste(…, ";"))` | collapses rows with the same ID, keeps IDs as text |
| `gather` | `bind_cols` / `pivot_wider` over many quantification files | format detection, version stripping |

**Name clash:** tidyr's `gather` (and csvtk's) means pivot to long format, the opposite of `detk-util gather`, which combines files into a wide matrix. A tidyr-inspired package next to detk would make that confusing. Under (c) the skill should say so.

#### What you need to decide

Choose (a), (b) or (c). If (c), also choose the tool (Miller or xan) and whether to add `detk-util record`. DETK-0051 would then be rewritten or superseded to match.

## Decision

Adam chose (c) with Miller and `detk-util record` (DETK-0051, which
records his answer). This record keeps the evidence for that answer;
accepting it means the finding is taken as the basis of DETK-0051, not
that any tool version above is pinned.

## How to reproduce

Install the tools named under Evidence examined from conda-forge into a
fresh environment (`conda create -n csvtools -c conda-forge miller xan
qsv duckdb-cli csvtk csvkit datamash`), write a sample sheet with the
rows described under Method, and run the commands quoted in the Finding
against it. Versions drift: the behaviours to recheck are IDs kept as
written, the standard deviation's denominator, and the result on a zero
and on a missing value. release/miller-recipes turns the Miller
commands into tested recipes, which is the lasting reproduction.
