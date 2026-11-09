---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/view-text, step: s1}
applies: [release/view-text]
allowed_by: [reasonable]
reason: "Option C of DETK-0014: the page sets every view text field as text, so no builder escapes and no user string becomes markup"
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
(`pca`, `deseq2counts-1`) and an unknown name cannot collide or break an
attribute; `data-mod` keeps the original id, which keys the raw data.

## Consequences

- No descriptor text field, module name or id can insert markup; the
  template's only `innerHTML` assignment is the static SVG (a test checks
  this). `tests/report/test_report_view_text.py` renders a report with a
  hostile string in each field and runs the page's own script in jsdom:
  zero injected elements and every string shown exactly as written; before
  the change the same report injected twelve `img` elements.
- Builders and `view_for` return plain text; `report_specs.py`'s module
  docstring says so. A builder that escapes would now show `&lt;` to the
  user (a test checks the notes are unescaped).
- The jsdom tests need node and jsdom and are skipped without them (CI
  installs neither); the template check runs everywhere. Adding jsdom to
  CI is a follow-up outside this node.
- A real report's cards (nine modules from `detk-norm`, `detk-filter` and
  `detk-stats`) build the same DOM tree as before.
- Revisit if a view needs real markup in its text; add a separate,
  explicitly HTML field then rather than making text fields HTML again.
