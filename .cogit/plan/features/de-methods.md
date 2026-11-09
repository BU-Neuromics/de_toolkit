---
kind: exploration
objective: 'de: which further DE methods detk offers through wrapr, edgeR quasi-likelihood, limma-voom or both (tracks #26)'
scope: [+de_toolkit/report_specs.py, +CHANGELOG, de_toolkit/de.py, de_toolkit/wrapr.py, docs/tools/de.md, tests/de/]
---

# Further DE methods: edgeR, limma-voom

## Implementation plan

- [ ] @explorer Try edgeR QL and limma-voom as candidates through wrapr and write the comparison record <!-- s1 -->
- [ ] @human Choose <!-- s2 -->

## Notes

#26 is labelled `decision`: pick the method set before writing code. Keep the `term__statistic`
column convention so `detk-enrich` stays method-agnostic; reuse the volcano and MA views.
