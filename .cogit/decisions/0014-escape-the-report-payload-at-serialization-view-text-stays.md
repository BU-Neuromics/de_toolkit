---
template: adr
state: Accepted
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/escape-json, step: s1}
applies: [release/escape-json]
allowed_by: [reasonable]
reason: "the script-block break is closed where the payload is made; moving view-text escaping into the template would change annotate's contract outside this node"
revisions:
  - {date: 2026-11-09, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-09: accept with release/escape-json"}
---

# Escape the report payload at serialization; view text stays HTML that builders escape

## Background

`detk-report` writes one self-contained HTML file. The module JSON (and a
per-module view descriptor built by `report_specs.py`) is embedded in two
`<script type="application/json">` elements and parsed by the page's own
script, which then builds each card with `innerHTML` from the descriptor's
text fields (`title`, `desc`, `note`, kv labels and values, table cells,
`error`). Many strings in that data come from user files: feature IDs,
sample names, column-data values, annotation columns and unmapped IDs from
`detk-util annotate` (#29, review of PR #41, issue #46).

## Context

Two distinct ways a user string can reach markup:

1. **The script block.** The payload was inserted with `|safe`, so a string
   holding `</script>` ended the element; the rest of the payload became
   HTML and the report broke. This is #46 and this node's objective.
2. **The card markup.** The page inserts the descriptor's text fields with
   `innerHTML`. The convention since annotate (#29) is that those fields are
   HTML and a builder escapes user strings in them (`build_annotate` runs
   `html.escape` on its note). Not every builder does yet: `build_filtercounts`
   puts the user's `--command` string in its note raw, and a builder
   exception's text goes into `error` raw.

Criteria: the report must never break on any user string; the fix should
sit where the data is made, be testable in Python, and stay within the
node's scope (`report.py`, `templates/report.html`, `tests/report/`).

## Options

- **A. Escape the payload at serialization (chosen for 1).** `report.script_json`
  translates `<`, `>`, `&`, U+2028 and U+2029 in the serialized JSON to
  `\uXXXX`. They occur only inside string literals, so the transform is
  safe on the whole text and `JSON.parse` returns the original strings.
  Testable without a browser; covers every current and future field.
- **B. Escape in the template with a Jinja filter** (`|tojson`-style).
  Same effect, but the escaping is invisible from Python and the existing
  `NumpyEncoder` output would have to pass through it anyway; no gain.
- **C. Also make the page escape every descriptor text field** (a JS `esc()`
  around `title`, `desc`, `note`, labels, cells, `error`). Closes path 2 for
  good, but changes the descriptor contract from "HTML" to "text": annotate's
  already-escaped note would be double-escaped unless `report_specs.py`
  (outside this node) changes in the same PR.
- **D. Keep the contract for path 2 and fix the unescaped builders** in
  `report_specs.py`. Also outside this node's scope.

## Decision

A for the script block. For the card markup, keep the current contract
(descriptor text fields are HTML; builders escape user strings) and do not
change the page's rendering in this node: C and D both reach into
`report_specs.py`, which this node's scope excludes, and the choice
between them (text vs HTML descriptors) shapes every future report view.

`NumpyEncoder` also wrote object keys raw between quotes, which made the
payload invalid JSON for a sample name with a quote or backslash used as a
key; keys are now JSON-encoded. That is a bug fix inside A, not a choice.

## Consequences

- No string in the module JSON can end or alter the payload's script
  elements; `tests/report/test_report_escape.py` covers sample names,
  column values, object keys and annotate's fields.
- Path 2 remains open: `build_filtercounts`' note (the user's filter
  command) and the raw-fallback `error` text are inserted unescaped.
  Follow-up: either escape them in their builders (D) or switch the page to
  text descriptors and drop `build_annotate`'s `html.escape` (C). C is the
  more robust choice; a follow-up node should take one of them before 1.0.
- Revisit if a view ever needs real markup from data other than the static
  SVG fallback, which stays HTML by design.
