---
kind: step
time: 2026-11-09T22:16:54Z
by: DETK/reviewer
node: release/view-text
step: s2
branch: node/65-view-text
verdict: changes
commits: []
decisions: []
---


# Re-review of #66: View Source is closed, but the chart tooltip is a second sink in vega-embed

## Summary

The View Source fix in 27fef47 is correct. The page now asks vega-embed for
`{ export: true, source: false, compiled: false, editor: false }`
(`report.html:271`). In the vendored vega-embed 6.29.0 the export path builds
two `<a>` elements with `.text` and a fixed `download` name. On mousedown it
sets `href` to `view.toImageURL(...)`, a Blob URL or a data URL. It writes no
markup and opens no window. The `wn()` function (`window.open("")` plus
`document.write`) and the editor's `postMessage` are reachable only through the
three actions that are now off. A hostile CLI report and a hand-written report,
with every action clicked, open no window, write nothing, and give SVG exports
with no `img`, `script`, `foreignObject` or handler attributes. The `_vis`
parity argument holds. The tests fail on main's template and pass on this
branch. The harness does fail on page errors and is not flaky.

There is one more sink of the same class, also inside vega-embed. The default
tooltip handler (vega-tooltip) sets `el.innerHTML = formatTooltip(value)`. Its
`sanitize` escapes only `&` and `<`. When the tooltip object has a key named
`image`, it writes `<img src="${new URL(sanitize(v), base).href}">`. For an
opaque URL such as `data:...`, `URL.href` leaves `"` as it is. So a value
`data:x"onerror="alert(document.domain)//` becomes
`<img src="data:x" onerror="alert(document.domain)//">`. The PCA builder uses
each covariate column's name as a tooltip title (`report_specs.py:92`). A
column-data file with a column named `image` therefore runs script on the
report's origin when a reader hovers a PCA point. This is reachable from the
CLI: `detk-stats pca counts.csv covs.csv`. The bug predates this PR, because
neither vega-embed nor the tooltip option changed. But it is the same class as
the View Source bug that the previous review asked to fix. With it open, two
claims overstate the result: DETK-0022's "no chart action writes the spec as
HTML ... no ... id can insert markup into the page", and the CHANGELOG's "can
no longer insert markup". The fix is in scope (`report.html`, plus a test in
`tests/report/`).

Changes are requested for that fix, as with View Source. Moving it to a
follow-up node is a reasonable alternative, but that is Adam's choice.

## Artifacts

All under
`/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/rr66/`.

- Branch head 27fef47, up to date with `origin/node/65-view-text`. It merges
  cleanly into fresh `origin/main` (`git merge-tree`). No repository file was
  changed.
- `cli/`: a hostile CLI report built with `detk-stats` (basestats, coldist,
  rowzero, colzero, entropy, pca), `detk-filter` and `detk-util annotate`.
  Sample names and feature IDs carry `"'><img onerror>`,
  `</code></pre><img ...>`, `<b>` and `&amp;`. The covariates are `image`,
  `title` and a quoted name. The repo harness found 0 injected elements,
  0 handlers, 0 alerts and 0 opened or written windows. Every embed was
  export-only and every menu showed only Save as SVG and Save as PNG. Four SVG
  exports had 0 injected elements and 0 handlers. No id was duplicated. The
  harness exited 1, correctly: the PCA chart failed with "Access path missing
  closing quote" on the quoted covariate name, which is the known, out-of-scope
  field-path issue.
- `cli2/`: the same report without the quoted covariate, so the PCA chart
  renders. The repo harness passes it (exit 0, all zeros). That is the gap: it
  never hovers.
- `tip.js`: loads a report with the harness's stubs and waits for every chart.
  For each scenegraph item that carries a `tooltip`, it calls the view's own
  tooltip handler, which is what a hover does. On `cli2`, all 6 tooltips held
  `<img src="data:x" onerror="alert(document.domain)//">`. Dispatching `error`
  on those images, as a browser does for an undecodable `data:` image, ran the
  handler 6 times (6 alerts). `node -e 'new URL("data:x\"onerror=\"a").href'`
  keeps the `"`.
- `fixtry.html`: the `cli2` report with
  `tooltip: { sanitize: <escape & < > "> }` added to the embed options. Tooltips
  show, 0 images carry `onerror`, and 0 alerts fire.
- `hand/`: a hand-written report: the real PCA module twice (giving `pca-1`),
  plus unknown modules `pca-vis`, `pca_vis`, `pca-1`, `X`, `X-vis`, `X_vis`,
  `X_5f_vis`, `__proto__`, `constructor`, `toString`, `main`, `nav`, `meta`,
  `theme-icon`, `theme-toggle`, `detk-raw`, `vg-tooltip-element`,
  `vega-embed-style`, `""`, `x` plus the test's `EVIL` string, `😀_`, `a b`,
  `#x`, `-`, and a filtercounts module with a hostile command. Results: 0
  injected elements, 0 handlers, 0 alerts, 0 opened windows, 0 page errors.
  Every "Show data" shows its own module (`__proto__`, `constructor` and
  `toString` included). Ids map as `X_vis` to `X_5f_vis`, `X_5f_vis` to
  `X_5f_5f_5f_vis`, `__proto__` to `_5f__5f_proto_5f__5f_`, and `😀_` to
  `_d83d__de00__5f_`. No card id equals a chart id. Duplicate ids:
  `pca-1` (the out-of-scope `{base}-{n}` collision) and `main`, `nav`,
  `meta`, `theme-icon`, `theme-toggle` and `detk-raw` (finding 2). With
  `tip.js`, the card named `vg-tooltip-element` became the tooltip host, and
  the card named `vega-embed-style` kept vega-embed's stylesheet out.
- `head/`, `maintpl/`, `mainall/`, `mutsrc/`: source copies run with
  `PYTHONPATH`. On this branch, 7 of 7 tests pass. With main's template, 6 of 7
  fail. With main's template and specs, 7 of 7 fail. With only `source: true`
  restored, 4 fail: the template check, the hostile-cards test, the chart
  actions test, and the collision test.
- `err/`: a kv view without `items` throws in the page script. The harness
  exits 1 with `Uncaught [TypeError ...]`.
- Flakiness: 36 runs of the jsdom tests, 12 in parallel, all passed. 8 more
  runs pinned to one core (about 31 s each) also all passed.
- `checks.log`: `uv sync` ok. `pytest` gives 313 passed, 49 skipped with
  NODE_PATH, and 309 passed, 53 skipped without it. `ruff check` passes.
  `ruff format --check` exits 0. `mkdocs build --strict` passes. `gh pr
  checks 66`: CodeQL, docs, ruff and tests on 3.11, 3.12 and 3.13 pass; "test
  with R (bioconda)" was pending.

Action and sink inventory for the vendored vega-embed 6.29.0
(`de_toolkit/templates/vega/vega-embed.min.js`; the README says only "6.x"):

| Path | Sink | Reachable now? |
|---|---|---|
| Save as SVG / PNG | `a.text`, `a.download`, `href = toImageURL()` (Blob or data URL) | yes; no markup, no window; Vega's SVG renderer escapes text |
| View Source / View Compiled Vega | `window.open("")` plus `document.write(json)`, unescaped | no (`source: false`, `compiled: false`) |
| Open in Vega Editor | `window.open(editorUrl)` plus `postMessage(spec)` | no (`editor: false`) |
| Tooltip (vega-tooltip `Handler`, on by default) | `el.innerHTML = formatTooltip(...)`; `sanitize` escapes `&<` only; `image` key goes to `<img src="URL.href">` | **yes, finding 1** |
| Tooltip style, embed style | `innerHTML` of a fixed CSS string (the style id is validated) | fixed text |
| Actions summary icon | `innerHTML` of a fixed SVG string | fixed text |
| `usermeta.embedOptions` in a spec | can re-enable actions or set the source header/footer | no builder writes `usermeta`; specs are fixed structures with user data only in `data.values` and titles |
| Embed error | page `.catch`: `target.textContent` | text |
| Page: "Show data" | `pre.textContent = JSON.stringify(...)` | text |
| Page: static SVG | `box.innerHTML = v.svg` (matplotlib) | the one intended markup site |

## Findings

1. **High**: `de_toolkit/templates/report.html:270-272`, reached via
   `de_toolkit/report_specs.py:92`. vega-embed's default tooltip handler
   writes tooltip HTML with `innerHTML`. Its sanitizer escapes neither `"` nor
   `>`, and a tooltip key named `image` becomes an `<img src>` whose URL
   (`data:` or any other opaque scheme) keeps `"`. A covariate column named
   `image` therefore injects `onerror` and runs script on hover, from the CLI
   (`tip.js` on `cli2`: 6 of 6 tooltips, 6 handlers ran). The bug predates
   this PR, but it is the same class as View Source, and DETK-0022 and the
   CHANGELOG claim it is closed. A fix in scope: pass the page's own
   `tooltip` options in the embed call. The minimum is a `sanitize` that
   escapes `&`, `<`, `>` and `"` (checked: `fixtry.html`). Better is a
   `formatTooltip` that ignores the `image` and `title` keys and renders
   every key and value as text, so a column named `image` also cannot make a
   local report fetch a remote URL on hover. Either way, add a jsdom test
   that drives the tooltip handler, as `tip.js` does, and extend the template
   check to cover the tooltip option. Then revise DETK-0022 (Decision and
   Consequences) and the CHANGELOG to name the tooltip.
2. **Low**: `de_toolkit/templates/report.html:165-181`. `domId` keeps ids made
   only of letters, digits and `-`. A hand-written module named after one of
   the page's own ids (`main`, `nav`, `meta`, `theme-icon`, `theme-toggle`,
   `detk-raw`, `detk-modules`, `tray-toggle`, `theme-label`) or one of
   vega-embed's (`vg-tooltip-element`, `vega-embed-style`,
   `vega-tooltip-style`) therefore duplicates that id. The harness's
   page-wide unique-id assert would fail on such a page. The observed effects
   involve no markup, only a hijack. The `vg-tooltip-element` card is used as
   the tooltip host, so its content is replaced on hover and the tooltip CSS
   (`visibility: hidden`) hides it. The `vega-embed-style` card keeps the
   actions menu's stylesheet out. The page's own lookups are unaffected,
   because the static elements come first in tree order or are read before
   the cards are built. Only hand-written JSON reaches this; CLI module names
   are fixed. One option is a reserved-name check in `domId` that escapes such
   ids (for example `main` to `_6d_ain`; the result is still injective and
   still has an even number of `_`). The other is to state the limit in
   DETK-0022, whose "two distinct ids never share a card id" is true, but
   whose test text says "unique ids across the page".
3. **Low**: `tests/report/render_dom.js:152`. After clicking every action, the
   harness waits a fixed 100 ms for the export hrefs. If an export is not done
   by then, `_no_markup` skips it (`svg is None`), so a slow run checks
   fewer exports instead of failing. Only
   `test_chart_actions_never_write_sample_names_as_markup` requires an SVG
   export to exist. I could not make it flaky (44 runs, 8 of them pinned to one
   core), so this is hardening only: await the `toImageURL` promise, or poll
   until every `download` link has a `blob:` or `data:` href.
4. **Info**: `docs/example/detk_report.html` is the published report built
   with the old template: `innerHTML` cards and `source: true`. It is not
   exploitable as it is. Its payload is the fixed airway example: 12 modules,
   the only markup characters are the `>=` in "filter command:
   nonzero(all) >= 0.5", and the PCA tooltip keys are `sample`, `PC1`,
   `PC2`, `cell` and `dex`. A reader cannot change it, so View Source and the
   tooltip only ever show benign data. It should still be rebuilt before the
   cut, after finding 1 is fixed, so the published example matches 1.0's
   menu and code and nobody reuses it as a template. That belongs to a docs
   or release task, not this node, as DETK-0022 says.
5. **Info**: `README.md` under `de_toolkit/templates/vega/` says vega-embed
   "6.x". The vendored file is 6.29.0 (`fn="6.29.0"`), and the tooltip
   behaviour above depends on that version. When the bundles are next pinned,
   record it.

Verified and fine: the `_vis` claim. Each non-`[A-Za-z0-9-]` code unit becomes
`_<hex>_`, and hex never contains `_`, so every `domId` output has an even
number of `_`. `cardId + "_vis"` has an odd number, so it never equals a card
id. Distinct card ids give distinct chart ids, and no static id ends in
`_vis`. `domId` is injective: literal characters never include `_`, so
decoding is unambiguous.

## Questions

- Finding 1: fix it in this PR (one embed option, a test, and DETK-0022 and
  CHANGELOG wording) or in a follow-up node? If it is a follow-up, DETK-0022's
  Consequences and the CHANGELOG entry need to stop saying the page and the
  charts cannot carry markup.
- Finding 4: who rebuilds `docs/example/detk_report.html` before the 1.0 cut,
  and is that a release checklist item?
