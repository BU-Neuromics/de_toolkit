---
kind: step
time: 2026-11-09T21:55:19Z
by: DETK/developer
node: release/view-text
step: s1
branch: node/65-view-text
verdict: done
commits: [3c9f12e, 86f1f30]
decisions: [DETK-0022]
---

# Done: Render every descriptor text field as text in the page's card builder; drop builders' own escaping; tests; CHANGELOG; open the PR

## Summary

The report page now builds each card with createElement/textContent: title, desc, notes, kv labels and values, table cells, the fallback error and an unknown module's name (card title, Show data button) render as text; id/href/data-mod are set as attributes and the card id is an injective safe fragment. The static SVG is the one innerHTML site left. build_annotate and build_gather no longer escape their notes. tests/report/test_report_view_text.py renders hostile strings in every field and runs the page's script in jsdom (0 injected elements; 12 img before), checks the static SVG still parses as SVG, and checks the template's only innerHTML is the SVG. A real 9-module report builds an identical card DOM. CHANGELOG Fixed entry. DETK-0022 (Provisional) records option C and names the DETK-0014 paragraph it would supersede, for Adam to confirm.

## Artifacts

## Findings

## Questions
