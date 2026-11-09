---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/view-text, step: s1}
applies: [release/view-text]
allowed_by: [reasonable]
reason: "Option C of DETK-0014: the page sets every view text field as text, so no builder escapes and no user string becomes markup"
revisions:
  - {date: 2026-11-09, by: DETK/developer, change: "Chart actions export only: View Source and Compiled and Editor off; chart ids end in _vis so no card id can equal one; pca-1 id collision noted as a follow-up", why: review of s2}
  - {date: 2026-11-09, by: DETK/developer, change: "Tooltip written as text by the page's own handler instead of vega-tooltip; card ids never equal the page's or vega-embed's reserved ids; harness awaits exports; old example report rebuild noted as a release task", why: second review of s2}
---

# View text fields render as text; builders no longer escape

## Background

`detk-report` writes one self-contained HTML page. For each module the page
reads a view descriptor built by `report_specs.py` (a title, a description
and a view: a chart, stat tiles, a table, a static SVG or a raw fallback,
each with optional `note` or `error` text) and builds the module's card from
it. Many of those strings come from user files or the command line: the
filter command, DE model term names (factor levels), annotation columns and
unmapped IDs, gather sample names and formats, an exception's message, and
an unknown module's name, which is also its card id.

DETK-0014 (Accepted) closed the payload's script block and kept, for the
card markup, the contract that view text fields are HTML and that builders
escape user strings in them. Its Consequences left that path open and named
two follow-ups, C (the page renders every text field as text) and D (fix
each builder). This record takes C. It would supersede DETK-0014's Decision
paragraph on view text, "For the card markup, keep the current contract
(descriptor text fields are HTML; builders escape user strings) and do not
change the page's rendering in this node", and the Path 2 bullet of its
Consequences; DETK-0014's choice A (escape the payload at serialization)
stands unchanged. It is Provisional for Adam to confirm; DETK-0014 is left
as it is.

## Context

The page inserted every text field with `innerHTML`. In the review of #55
hand-written module JSON put four `img[onerror]` elements into the page in
jsdom: through the filter command, a DE term name in the sampling note, an
unknown module's name in its card title, and the module id in the card's
`id`, `href` and `data-mod` attributes (an attribute break with a quote).
Only `build_annotate` and `build_gather` escaped their notes; every other
builder, the error fallback in `view_for` and the unknown-module entry
passed user strings through raw.

Criteria: no user string can become markup in any field, now or in a view
added later; the fix is testable by running the page; the page looks the
same for ordinary data; the change stays within this node's scope
(`templates/report.html`, `report_specs.py`, `tests/report/`).

## Options

- **C. Text descriptors: the page sets every text field as text.** The card
  builder uses `createElement` and `textContent` for the title, description,
  notes, kv labels and values, table headers and cells and the error;
  attributes are set with `setAttribute`, and a module id becomes a safe
  fragment for the card id and link. Builders pass user strings through
  unescaped, so `build_annotate` and `build_gather` drop `html.escape`.
  Closes the whole path in one place, including for future builders, which
  cannot forget to escape. Cost: a view can no longer put markup (bold, a
  link) in a note; none does today.
- **D. Keep HTML descriptors and escape in every builder.** Fix
  `build_filtercounts`, `_build_de`'s two notes, the `view_for` error and
  unknown-module entries. Leaves the page unchanged, but every future
  builder must remember to escape, and the module id in attributes needs
  escaping in the page anyway; one missed field reopens the hole.
- **C with an opt-in HTML field.** As C, plus a separate `note_html` for a
  view that needs markup. No view needs it; adding it later is easy, so it
  is left out.

## Decision

C. It removes the class of bug rather than its current instances: the page
is the one place every field passes through, and the only markup it inserts
is the static SVG (`view.svg`), which `static_plots` renders with
matplotlib from numbers and escapes its own text. A module id is encoded as
an injective fragment (letters, digits and `-` kept; any other code unit,
`_` included, written `_<hex>_`), so registered modules keep their ids
(`pca`, `deseq2counts-1`), two distinct ids never share a card id, and an
unknown name cannot break an attribute; `data-mod` keeps the original id,
which keys the raw data. A module named like one of the ids the page or
vega-embed give their own elements (`main`, `nav`, `meta`, `tray-toggle`,
`theme-toggle`, `theme-icon`, `theme-label`, `detk-modules`, `detk-raw`,
`detk-tooltip`, `vg-tooltip-element`, `vega-embed-style`,
`vega-tooltip-style`) also has its first character escaped (`main` becomes
`_6d_ain`); a letter is otherwise never escaped, so the encoding stays
injective and no card can take one of those ids. No registered module's
id is reserved, so theirs are unchanged. A card's chart container is the card id plus
`_vis`: every `domId` output holds an even number of `_`, so no card id can
equal a chart id (with `-vis`, an unknown module named `pca-vis` took the
PCA chart's id).

The same rule reaches the charts' action menu. vega-embed's "View Source"
and "View Compiled Vega" write the spec's JSON, unescaped, as HTML into a
`window.open("")` page that shares the report's origin, so a sample name in
a chart's data would run as script there; "Open in Vega Editor" posts the
spec, with every sample and feature name, to vega.github.io. The page turns
all three off and keeps only "Save as SVG" and "Save as PNG", which download
a file and draw names as text (Vega's SVG renderer escapes them). "Show
data" on each card is the way to see a module's data, as text.

The charts' tooltip is the same sink. vega-embed's default tooltip handler
(vega-tooltip, in the vendored vega-embed 6.29.0) sets `innerHTML` from a
formatter that escapes only `&` and `<` and turns a field named `image`
into `<img src="...">`; a `data:` URL keeps its `"`, so a covariate column
named `image` (the PCA chart puts every covariate in its tooltip) could add
an `onerror` handler that runs on hover. The page passes its own tooltip
handler instead: it writes every key and value as text with `textContent`,
gives no key special meaning and loads nothing.

## Consequences

- No descriptor text field, module name or id is inserted as markup by
  the card builder, no chart action writes the spec as HTML, and the chart
  tooltip writes text only; the template's only `innerHTML` assignment is
  the static SVG, its vega-embed actions are export only and its embed call
  passes the page's tooltip handler (template tests check all three). This
  covers the page's own code and the vega-embed paths it leaves on; Vega's
  own canvas and SVG drawing of chart text is relied on, not re-checked. `tests/report/test_report_view_text.py`
  renders a report with a hostile string in each field and runs the page's
  own script in jsdom, Vega charts included: zero injected elements, every
  string shown exactly as written, every tooltip (driven through the view's
  own tooltip handler for every mark that has one) shown as `key: value`
  text with no element but `div` and `span` and no handler, no window
  opened when every chart action is clicked, every export awaited and
  checked, and unique ids across the page, modules named like the
  reserved ids included; before the change the same
  report injected twelve `img` elements, and with View Source on, a
  hostile counts header put 42 `img` elements into the source windows, and
  with vega-embed's default tooltip a covariate column named `image` put an
  `img[onerror]` into each of six PCA tooltips (six handlers ran).
- Builders and `view_for` return plain text; `report_specs.py`'s module
  docstring says so. A builder that escapes would now show `&lt;` to the
  user (a test checks the notes are unescaped).
- The jsdom tests need node and jsdom and are skipped without them (CI
  installs neither); the template check runs everywhere. Adding jsdom to
  CI is a follow-up outside this node.
- A real report's cards (nine modules from `detk-norm`, `detk-filter` and
  `detk-stats`) build the same DOM tree as before.
- Follow-up outside this node: `report.py` numbers a second module of the
  same name `{base}-{n}` (`pca-1`), which can equal a module really named
  `pca-1`; the two cards then share an id and one's "Show data" shows the
  other's JSON. `domId` cannot fix this, since its input is already
  duplicated. Also outside it: a covariate name holding a quote, `.` or `[`
  breaks the PCA chart's field access (a chart error, not injection).
- The checked-in `docs/example/detk_report.html` was built with the old
  template: `innerHTML` cards, View Source on and vega-embed's default
  tooltip. Its data is the fixed airway example with no markup in it, so it
  is not exploitable as published, but it should be rebuilt before the 1.0
  cut so the published example matches this template; that is a separate
  release task, not this node.
- The tooltip behaviour above depends on the vendored vega-embed version
  (6.29.0; its README says only "6.x"). Pinning it there is outside this
  node.
- Revisit if a view needs real markup in its text; add a separate,
  explicitly HTML field then rather than making text fields HTML again.
