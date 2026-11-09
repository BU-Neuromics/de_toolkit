---
kind: task
objective: 'No string in a report view''s text fields becomes markup: every descriptor field is rendered as text (option C of DETK-0014)'
acceptance:
  - every view descriptor text field renders as text, except the static SVG markup, which stays markup
  - 'the filter note, the DE capped and static-SVG notes (term names), the fallback error, and an unknown module''s name and id (in the card''s title, its id, href and data-mod attributes and the Show data button text) render hostile strings as text, shown with a test that builds the cards'
  - build_annotate and build_gather no longer escape their own notes, and no builder needs to
  - 'the change from DETK-0014 (view text stays HTML that builders escape) is recorded: a record of this node supersedes or amends DETK-0014'
scope: [de_toolkit/templates/report.html, de_toolkit/report_specs.py, tests/report/, +CHANGELOG]
prev: [release/escape-json]
issue: 65
visited: 74632ba
---

# Render all view text as plain text

## Implementation plan

- [x] @developer Render every descriptor text field as text in the page's card builder; drop builders' own escaping; tests; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Acceptance revised 2026-11-09 from the review of de_toolkit#57.

Planned 2026-11-09 on Adam's word. From the review of de_toolkit#55 (escape-json): view descriptor text fields reach innerHTML unescaped; DETK-0014 records the options.
