---
kind: task
objective: 'No string in a report view''s text fields becomes markup: every descriptor field is rendered as text (option C of DETK-0014)'
acceptance:
  - the filter note, the DE capped and static-SVG notes (term names), the fallback error and an unknown module's name render hostile strings as text, shown with a test that builds the cards
  - build_annotate no longer escapes its own note, and no builder needs to
scope: [de_toolkit/templates/report.html, de_toolkit/report_specs.py, tests/report/, +CHANGELOG]
prev: [release/escape-json]
---

# Render all view text as plain text

## Implementation plan

- [ ] @developer Render every descriptor text field as text in the page's card builder; drop builders' own escaping; tests; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word. From the review of de_toolkit#55 (escape-json): view descriptor text fields reach innerHTML unescaped; DETK-0014 records the options.
