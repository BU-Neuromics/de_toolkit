---
kind: step
time: 2026-11-09T22:01:54Z
by: DETK/reviewer
node: release/view-text
step: s2
branch: node/65-view-text
verdict: changes
commits: []
decisions: []
---


# Review of #66: view text renders as text, one sink left in vega-embed's View Source

## Summary

The card builder change is correct and complete for the page's own code. Every
descriptor text field, module name and id now reaches the DOM through
`textContent` or `setAttribute`. The one `innerHTML` left is `v.svg`, and
matplotlib escapes the term name that it writes into that SVG. A real
nine-module report (norm library, filter, stats summary and basestats,
annotate) builds a byte-identical `#nav`/`#main` DOM under main's template and
this branch's. The new tests fail on main's template and specs (3 of 4 fail,
including 15 injected elements in the hostile-cards test) and pass here.
DETK-0022 states fairly what it would supersede in DETK-0014, and DETK-0014 is
untouched.

One sink remains, and it is reachable from the CLI. The page asks vega-embed
for its "View Source" action (`source: true`). vega-embed 6.x writes the spec's
JSON into a new `window.open("")` document with `document.write`, with no
escaping. That about:blank window inherits the report's origin. A sample name
in a counts header such as `</code></pre><img src=x onerror=...>` therefore runs
script when a reader opens the chart's "..." menu and clicks View Source. The
bug is older than this PR (main has `source: true`), but it is exactly the
class of bug this node's objective sets out to close. The new CHANGELOG entry
("can no longer insert markup into the page") and DETK-0022 ("No descriptor
text field ... can insert markup") overstate the result while it stays open.
The fix is one line, in scope: `source: false` in `report.html:263`. If the
source view matters, the page could instead add its own action that sets the
JSON as `textContent`. Changes are requested for that fix. Splitting it into a
follow-up node is a reasonable alternative, but that choice is Adam's.

## Artifacts

- Hostile CLI report: counts header, feature IDs, covariate name and values,
  and annotate map column and unmapped IDs, all carrying `"'><img onerror>`,
  `</code></pre><img onerror>`, `</title>`, `--><img>`, `<b>` and `&amp;`. It
  was built with `detk-filter`, `detk-stats summary|basestats|coldist|colzero`
  and `detk-util annotate`. jsdom result on the page: 0 injected elements,
  0 handler attributes, 0 alerts. The annotate note shows the IDs exactly as
  written.
- The same report with View Source clicked (vega-embed with the svg renderer,
  `window.open` stubbed to capture `document.write`): coldist's source document
  contains 40 `<img onerror>` elements and colzero's contains 2. Entropy and
  rowzero carry no sample names and stay clean.
- Hand-written module JSON for the id edge cases (`""`, `__proto__`,
  `constructor`, `a.b` against `a_2e_b`, `xéy`, `colzero-vis`):
  - `domId` stays injective (`a.b` maps to `a_2e_b`, `a_2e_b` to `a_5f_2e_5f_b`).
  - Show data finds the right raw entry for `__proto__` and `constructor`.
  - The unknown `colzero-vis` card collides with colzero's chart div (finding 2).
- Static SVG: a hostile title rendered by `scatter_svg` appears only as an XML
  comment, escaped by matplotlib (`&lt;`, `&gt;`, `--` becomes `- -`). There is
  no `<title>` element and no raw text.
- Tests on main: with main's template, 3 failed and 1 passed (template check;
  15 injected elements; 1 injected element in the static-SVG note). With
  main's report_specs as well, `test_builders_leave_notes_unescaped` also fails.
- Checks: `uv sync` ok. `pytest` gives 310 passed and 49 skipped (R and fgsea
  only; the jsdom tests ran with NODE_PATH set). `ruff check` passes.
  `ruff format --check` exits 0. `mkdocs build --strict` passes. `gh pr checks
  66`: all pass except "test with R (bioconda)", which was still pending.
- `git merge-tree` against fresh origin/main: merges cleanly.

## Findings

1. **High**: `de_toolkit/templates/report.html:263`. `actions: { source: true }`
   enables vega-embed's View Source. It `document.write`s the unescaped spec
   JSON into a same-origin about:blank window, so sample names, covariate
   names and values, and pathway, feature or term names in `data.values` or
   titles become markup there. This is reachable from the CLI with a hostile
   counts header and is older than this PR. Fix: `source: false`, or an action
   of the page's own that shows `JSON.stringify(spec)` via `textContent`. The
   CHANGELOG entry (`CHANGELOG:71-75`) and DETK-0022's Consequences should only
   claim "no markup" once this is closed. The tooltip handler is safe: its
   `sanitize` escapes `&` and `<`. Titles and labels are drawn on canvas.
2. **Low**: `de_toolkit/templates/report.html:202`. `cardId + "-vis"` is in
   `domId`'s output range. An unknown module named `X-vis` gets card id `X-vis`,
   which duplicates module X's chart div. Shown with `colzero-vis`: the nav link
   `#colzero-vis` goes to colzero's chart. `embedAll` still finds the right
   element only because "other" sorts last. This is not injection, but
   DETK-0022 says an unknown name "cannot collide" (`.cogit/decisions/0022-...md:81`).
   Fix: a suffix that `domId` can never produce, such as `cardId + "_vis"`
   (`domId` writes `_` only as `_<hex>_`, and `v` is not hex).
3. **Low, pre-existing, outside scope**: `de_toolkit/report.py:285`.
   `dom_id = f"{base}-{n}"` collides with a module really named `pca-1` when two
   `pca` modules exist: the ids are duplicated and `raw[dom_id]` is overwritten,
   so Show data on one card shows the other's JSON. Worth a follow-up.
   `domId` cannot fix it, because its input is already duplicated.
4. **Low**: `tests/report/test_report_view_text.py:48` and
   `tests/report/render_dom.js:15`. The DOM tests are skipped in CI (no jsdom),
   so the regex template check (`:163`) is the only CI guard. Separately, the
   harness collects jsdom errors but asserts nothing about them. Under
   jsdom/Node, vega-lite throws `structuredClone is not defined`, so no chart
   ever renders in these tests and Vega's output and actions (finding 1) are
   never exercised. A `w.structuredClone` polyfill in `beforeParse` makes
   embedding run. The skip is acceptable as DETK-0022's stated follow-up. The
   follow-up should also add a View Source or Vega check.
5. **Info**: `tests/util/test_annotate.py:151`. The edit is outside the node's
   scope but forced by acceptance item 3: the old assertion that `<b>` is
   absent from the note fails once `build_annotate` stops escaping. The new
   assertion is the right one.
6. **Info**: the PCA chart fails with "Access path missing closing quote" when a
   covariate name holds a quote, and a name with `.` or `[` is read as a nested
   path. This comes from Vega-Lite's field strings: it degrades to "chart
   error" and is not injection, because vega-util quotes the accessor code. It
   is older than this PR. A follow-up could escape field names with `\\`.

## Questions

- Should the View Source fix (finding 1) land in this PR, or go to a follow-up
  node, with the CHANGELOG and DETK-0022 wording narrowed to "card text" in the
  meantime?
- DETK-0022 is Provisional, and a human needs to confirm it to supersede the
  Decision paragraph and Path 2 bullet of DETK-0014. Its text is fair. Its
  "cannot collide" sentence needs finding 2's fix or a softer wording.
