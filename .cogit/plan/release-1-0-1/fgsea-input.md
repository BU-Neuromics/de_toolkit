---
kind: task
objective: the fgsea crate action lists the DE results file as an input beside the GMT file, so the enrichment table links to the DE step that wrote its ranking
acceptance:
  - 'reproduced first as a test: on v1.0.0 the crate action of ''detk-enrich fgsea -c ... gene_sets.gmt de.csv'' has object gene_sets.gmt and the params but not de.csv, though argv names it. After: object holds both files (in_file_paths), and the module JSON''s in_file_path stays the GMT'
  - CHANGELOG 1.0.1 entry
scope: [de_toolkit/enrich.py, +tests/enrich/, +tests/report/, +CHANGELOG]
---

# fgsea records the results file it ranked as an input

## Implementation plan

## Notes
