# Writing a tutorial page

A tutorial is a docs page that is also an integration test (DETK-0064). Its
```` ```bash ```` blocks run in order, as one pytest test, and the outputs it
shows are checked. This page says how to write one and its checks. The runner
is `tests/tutorials/tutorial_runner.py`; its own tests run it on the fixture
pages in `tests/tutorials/pages/`, which are small worked examples of every
marker.

## Where pages go

- `docs/tutorials/<name>.md`: every page here except `index.md` is a
  tutorial. Add it to the nav under Tutorials in `mkdocs.yml` and give it a
  row in `docs/tutorials/index.md` that says what it needs.
- Any other page under `docs/` (a recipe, say) becomes a tutorial by carrying
  a marker: `<!-- tutorial -->` on a line of its own, or any of the markers
  below.

## How a page runs

- Every ```` ```bash ```` block runs, in the order of the page, with
  `bash -euo pipefail`: a failing command, a failing stage of a pipe or an
  unset variable fails the block.
- Each page starts in a fresh, empty working directory (under pytest's
  temporary directory), so it must make or fetch everything it uses.
- Files, shell variables (exported or not), functions and the current
  directory carry from one block to the next, as in a reader's terminal.
- The detk of the test session is first on `PATH`.
- `TUTORIAL_SRC` is the directory that holds the page, for a hidden block
  that copies data committed next to it (`cp -r "$TUTORIAL_SRC/data" .`),
  when the visible page tells the reader where to get those files.
- Blocks in other languages are shown and not run: use ```` ```console ````
  for a command the reader should see but the test should not run (an
  install line, say), and ```` ```r ```` or ```` ```python ```` for code shown
  for reading.
- A block may run for 30 minutes before it counts as failed.

## Markers

Markers are HTML comments, so they do not show on the site. Each is on a line
of its own.

### requires

````markdown
<!-- tutorial: requires R DESeq2 airway -->
<!-- tutorial: requires mlr -->
````

What the page needs, near its top. `R` followed by R package names needs
`Rscript` and those packages; anything else is a program that must be on
`PATH`. Where one is missing the test is skipped and the reason says what is
missing (`pytest -rs` shows it). The CI job with R sets
`DETK_TUTORIALS_REQUIRE_ALL=1`, which makes a missing requirement a failure,
so a tutorial cannot skip there unnoticed.

### expect

````markdown
```bash
detk-stats summary counts.csv | head -n 3
```

<!-- tutorial: expect -->
```text
...
```
````

Right before a fenced block (blank lines between are fine, prose is not):
that block is the output of the bash block before it, and is compared with
what the block printed to stdout. Trailing spaces and blank lines at the ends
are ignored. `...` matches any text, including several lines, which is the
way to show a number that varies past a few digits (`0.0412...`), a date or
a run time. Options:

- `<!-- tutorial: expect regex -->`: the block is a Python regular
  expression that must match the whole output. Use it sparingly; a reader
  sees the pattern.
- `<!-- tutorial: expect stderr -->` or `expect stdout`: which stream to
  compare. stdout is the default, but stderr after a `fails` block.

Show outputs that teach something; a command whose output a reader does not
need to see does not need an expect.

### fails

````markdown
<!-- tutorial: fails -->
```bash
test "$(wc -l < coldata.csv)" -gt 100
```

<!-- tutorial: expect -->
```text
...
```
````

Right before a bash block: the block must exit non-zero (a check that rejects
a bad value, say). An expect after it compares its stderr. Files and
variables the failing block made do not carry to the next block.

### hidden

````markdown
<!-- tutorial: hidden
```bash
test -s results/deseq2.csv
```
-->
````

The bash blocks between `<!-- tutorial: hidden` and a `-->` on its own line
run but are not shown on the site (the rendered code stays inside the HTML
comment). Keep these rare: a check worth making is usually worth showing.

## Deeper checks: tests/tutorials/test_&lt;page&gt;.py

For checks that would not help a reader (results against DESeq2 run
directly, numbers against numpy), add `tests/tutorials/test_<page>.py`. The
`tutorial_workdir` fixture runs the page (once per test session, shared with
the page's own test) and returns its working directory after the last block:

```python
def test_airway_results_match_deseq2(tutorial_workdir):
    workdir = tutorial_workdir("tutorials/airway.md")
    results = pandas.read_csv(workdir / "deseq2_results.csv", index_col=0)
    ...
```

If the page was skipped this test is skipped too; if the page failed, it
fails, naming the page's failure.

## Running and debugging

```console
$ uv run pytest tests/tutorials -k airway          # one page
$ uv run pytest tests/tutorials -rs                # all, with skip reasons
$ uv run --group docs mkdocs build --strict        # the page renders
```

A failing block reports `page.md:<line of the block>`, the block, and the
tail of its stderr and stdout; a mismatched output reports the line of the
expected block and both texts. The scripts the runner ran are kept in the
working directory's `.tutorial/` (one per block, named by its line), so
`pytest --basetemp=out` leaves them where you can run them by hand.

## In CI

The test jobs (no R) run every tutorial that needs no R or Miller; the
others skip. The job with R installs Miller as well and sets
`DETK_TUTORIALS_REQUIRE_ALL=1`, so it runs every tutorial. Both run
`pytest tests`, which includes `tests/tutorials/`. The detk commands a page
runs are separate processes, so they do not add to the coverage report.
