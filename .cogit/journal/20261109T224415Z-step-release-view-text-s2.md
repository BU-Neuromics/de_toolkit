---
kind: step
time: 2026-11-09T22:44:15Z
by: DETK/reviewer
node: release/view-text
step: s2
branch: node/65-view-text
verdict: approve
commits: []
decisions: []
---


# Third review of #66: no reachable sink left; user strings stay text in every path the page leaves on

## Summary

Reviewed at 0f66d01 (`node/65-view-text`, up to date with origin). The diff against freshly fetched `origin/main` merges cleanly (`git merge-tree`), and GitHub reports MERGEABLE.

The two fixes are correct. The embed call passes `tooltip: showTooltip` (`report.html:334`), and vega-embed 6.29.0 uses a function as the view's handler as given. So vega-tooltip's `Handler` is never constructed: no `#vg-tooltip-element`, no `vega-tooltip-style`, no `innerHTML`. `showTooltip` (`report.html:291-319`) writes each key and value with `textContent` into `div`/`span`. It gives no key special meaning and loads nothing. `domId` (`report.html:179-188`) moves the 13 reserved ids off their own names. The result stays injective, because a letter is otherwise never escaped and the escaped form still has an even number of `_`.

I then took a full inventory of what the page can do with data (below). That covers the page's own JS and every vega-embed, Vega and Vega-Lite path left reachable, including expression evaluation. I found no path by which a user string becomes markup or script, opens a window, navigates, or loads a remote resource. The test is hostile reports built from the CLI and from hand-written module JSON, with every sink instrumented in jsdom. A negative control (the same report with the old tooltip and View Source re-enabled) is caught by the same probe, so the probe is sensitive.

The remaining findings are low or informational. None is markup injection and none blocks.

## Artifacts

Scratch: `/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/r3-66/`

- `drive.js` is the instrumented jsdom driver. It hooks the `innerHTML`/`outerHTML` setters, `insertAdjacentHTML`, `document.write`, `createContextualFragment`, `setAttribute` of href/src/on*, `window.open`, `postMessage`, `fetch`, XHR, string `setTimeout`, and a MutationObserver over every added element. It hovers every tooltip item through the view's own handler and fires pointer and click events at each canvas. It clicks every action and awaits every export, then parses the SVG exports. It clicks Show data three times per card, every nav link, the tray toggle and the theme toggle twice (which re-embeds), then checks for duplicate ids and for `Object.prototype` pollution.
- `cli/`, `cli2/` hold CLI reports. Sample names, feature IDs and the filter command are hostile. The covariate columns are `image`, `href`, `url`, `title`, `description`, `cursor`, `tooltip`, `text` and `status`, with `data:x"onerror=...`, `javascript:` and `<img onerror>` values. The annotate mapping column and its values are hostile too. Modules: basestats, coldist, rowdist, colzero, rowzero, entropy, pca, filter ×2, norm deseq2/library/cpm, transform plog, outlier entropy/shrink, util annotate (14).
- `hand/` is a hand-written report with 57 cards: DE with hostile terms (bound select), static DE with more than 20000 points, fgsea, annotate, gather, filter, basestats/shrink with object values, pca with 12 hostile covariate names, fpkm, rlog, the bar charts, and 37 unknown names. Those names cover reserved ids, `_6d_ain`, `pca_vis`, `__proto__`, `constructor`, `vegaEmbed`, `process`, `define`, `VEGA_DEBUG`, `DejaVuSans-48`, `""`, emoji, and a module JSON carrying its own `view`/`title`/`id`.
- `hexpr/` holds module JSON values that are Vega-Lite expression objects: `{"expr": ...}` and `{"signal": ...}` thresholds, a DateTime threshold, an expr y-max, an expr DE term, and a covariate name ending in `\`.
- `exprs.js`, `fuzz.js`, `fuzz2.js`, `astall.js` compile every builder's spec with the vendored Vega-Lite 5.23.0, parse every Vega expression, and compare identifiers and callees with a benign baseline.
- `neg.html` and `neg.out.json` are the negative control. `*.out.json` hold the driver results. `checks.log` holds the check results.

## Findings

1. **Low: matplotlib's ids in the static SVG are not reserved** (`report.html:170-172`, `:234`). A static DE chart (more than 20000 points) defines about 49 ids that `domId` can produce: glyphs `DejaVuSans-XX`, markers `m<hex>`, `image<hex>`. An unknown module named `DejaVuSans-48` gets the card id `DejaVuSans-48`, so the hand report has one duplicate id. Unknown modules sort last (family `other`), so the SVG's `<use xlink:href="#DejaVuSans-48">` still finds the glyph. The only effect is that the nav link for that card jumps to the glyph. Nothing becomes markup, and the case needs a hand-written module name. Independently of user input, two static SVGs on one page already share all their glyph ids. Leaving this as it is, or noting it in DETK-0022's Consequences next to the reserved list, is fine. It does not block.
2. **Informational: a spec's `usermeta.embedOptions` would override the page's embed options.** In vega-embed 6.29.0 the merge is `{...mergeDeep(callerOpts, usermetaOpts)}`, so the spec wins. A spec with `usermeta: {embedOptions: {actions: true, tooltip: true}}` would restore View Source and vega-tooltip. I confirmed this in jsdom with `usermeta.html`, a cli2 copy with that `usermeta` added by hand to the first spec: vega-tooltip's `innerHTML` came back, and the Source, Compiled and Editor actions opened windows. This is not reachable today: every spec is built by a `report_specs` builder, none emits `usermeta`, and a module JSON's own `view` key is ignored (the hand report includes one). A possible hardening, not a request: drop `usermeta` from each spec before `vegaEmbed`, or add a template or test check that no builder emits it.
3. **Informational: Vega-Lite 5.23.0 escapes tooltip and description keys only for `"`.** It does not escape `\`, newline or U+2028. A PCA covariate named `c\`, `\"` or with a newline therefore gives `chart error: Expression parse error: ...`, shown as text. Is it an expression injection? Each key's field occurs three times, and `: ""+` forces two adjacent string literals. Because of that, the single-quote parity before `""` is always even, so the injected text cannot close the expression cleanly. Fuzzing found none in about 580k compiled candidates over quotes, backslashes, dots, brackets and `upper(1)` markers: 400k as PCA tooltip and colour fields, 180k as text datum, select param and multi-field tooltip. This sits next to the out-of-scope PCA field-path errors, so I am not asking for anything.
4. **Informational: Vega's bar charts drop every mark when a sample is named `__proto__`, `constructor` or `toString`.** Vega's aggregate throws `c.push is not a function`. There is no chart error and `Object.prototype` is not polluted (checked). This is inside Vega, outside this node.
5. **Informational: no Vega expression is evaluated from user data.** `{"datum": {"expr"|"signal": ...}}` from a hand-written `threshold` or y-max fails Vega-Lite compile ("Invalid field type"). A DE term object becomes the signal's literal `value` (`sel_term` read back as the object). A DateTime is normalized and its label is JSON-escaped. Across all four reports, every callee in compiled expressions is in the Vega-Lite vocabulary.
6. **Informational, test hygiene:** running `pytest` writes `ro-crate-metadata.json` into the working directory. It is gitignored, so harmless.

## Sink inventory (what the page does with data, and what each reaches)

Page JS (`de_toolkit/templates/report.html`):
- `JSON.parse` of `#detk-modules` and `#detk-raw`. The payload is escaped by `script_json` (DETK-0014).
- `#meta`: a number via `textContent`.
- Card builder `el()`: `textContent` for title, desc, note, kv value and label, th/td, error, button text.
- `setAttribute` for `href="#"+domId`, `data-mod` (raw id), `dataset.target`. `card.id` and `vis.id` come from `domId`. `domId` emits only `[A-Za-z0-9_-]`, is injective, and avoids the reserved and `_vis` ids.
- `box.innerHTML = v.svg` is the only HTML site. Its input is matplotlib output, where text is escaped and title comments are de-dashed: a hostile term gives `<!-- volcano: big"'&gt;&lt;img ... ]]&gt;- -!&gt;&lt;!- - -->` and 0 script, img, foreignObject or handler elements.
- `families[m.family]`: the family is always fixed or `other`, never user data.
- Show data: `raw[data-mod]` lookup with `JSON.stringify` into `pre.textContent`. `__proto__` and `constructor` modules are own keys from `JSON.parse`, and the output is text.
- nav click: `classList` only. Tray and theme: `localStorage` is compared, `textContent` is fixed. Theme re-embeds.
- `showTooltip`: `textContent` only. Its id is reserved. Its style is `left`/`top` numbers.
- The embed catch writes `"chart error: "+err` via `textContent`.

vega-embed 6.29.0:
- `actions` = export only. SVG and PNG are `<a>` elements with `.text` and fixed `download`; `href` is a blob or data URL from `toImageURL`. `wn()` (`window.open("")` plus `document.write`) and the editor's `postMessage` are unreachable.
- `innerHTML` writes in vega-embed: the default style (constant), the summary icon (constant), the container (`""`), and vega-tooltip's two writes, which are unreachable because the page passes a function.
- A string spec would trigger a URL load; specs are always objects.
- `usermeta.embedOptions` merge: see finding 2, unreachable.
- `$schema` is parsed for a version warning only and never fetched.
- `loader`, `patch` and `config` URLs come only through options or usermeta.

Vega 5.33.1:
- Canvas renderer: text is drawn, never parsed. SVG export writes escaped text and attributes; every export parsed as `svg` with 0 handlers, 0 href and 0 injected elements.
- Bound select for the DE term: `option` value and `textContent`, checked with `</select><img>` terms.
- `href` handler, `image` marks, `data.url`, `cursor`: no builder emits them, and none of the compiled specs contains an href, url, image or cursor encoding. Columns named `href`/`image`/`url` stay data.
- Expressions: see findings 3 and 5. `field()` uses a getter, not `Function`. `VEGA_DEBUG` is absent in 5.33.1. DOM clobbering via card ids (`process`, `define`, `vegaEmbed`) was tried: harmless, and the UMD wrappers run before the cards exist.

## Hostile-input evidence

- cli2 (14 cards): 329 tooltips shown, 0 non-div/span elements, 0 handlers. The PCA rows read `image: data:x"onerror="alert(document.domain)//` as text. 0 `innerHTML` writes of user data (only the constant style, summary icon and container clears). 20 exports: 0 injected, 0 handlers, 0 href. 0 windows, 0 writes, 0 postMessage, 0 network, 0 alerts, 0 page errors. Location stays on `#fragment` links. 0 duplicate ids. `Object.prototype` is clean.
- cli (with a `__proto__` sample): the same, except that the bar charts are empty (finding 4).
- hand (57 cards): the same. The one HTML sink holding hostile text is the matplotlib SVG, and its parsed result has 0 bad elements and 0 handlers. Select options are shown as text. Duplicate ids: `DejaVuSans-48` only (finding 1).
- hexpr: chart errors shown as text, no expression evaluated.
- Negative control (`tooltip:` line removed, source and compiled re-enabled): the same driver sees `img[onerror]` in vega-tooltip, 2 alerts fired, 20 source windows written with `<img`, and remote `img` loads (`http://evil.example/x.png`).

## Checks

- `uv sync`: OK.
- `uv run pytest`: with NODE_PATH, 367 passed and 49 skipped. Without it, 360 passed and 56 skipped; the 7 jsdom tests skip with a reason.
- The new tests fail where they should. On main's code with this branch's tests, 11 of 11 fail. On this branch with the template before 0f66d01, 7 of 11 fail.
- Flakiness: 10 runs, 11 of 11 every time, 4.3 to 4.8 s. 3 more runs pinned to one CPU at nice 19 also passed.
- `ruff check`: passes. `ruff format --check`: exit 0.
- `mkdocs build --strict`: exit 0.
- `gh pr checks 66`: all pass, including test with R (bioconda) and combined coverage.

## Questions

None. Findings 1 and 2 are optional hardening, for Adam to take or leave. Finding 3 belongs with the PCA field-path follow-up that is already out of scope.
