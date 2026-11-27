---
kind: task
objective: detk-enrich fgsea without -c/--statcol is a usage error when the results table has more than one numeric column besides the ID column, and the ranking it used is recorded (DETK-0600)
acceptance:
  - 'reproduced first as a test: on a DESeq2 results table (11 numeric columns) v1.0.0 ''detk-enrich fgsea -o out.csv gene_sets.gmt de.csv'' exits 0 and ranks by condition__treated__padj (the audit''s planted ''up'' set: NES -2.76, padj 0.5; with -c condition__treated__stat NES +2.13, padj 0.0003). After: exit 2, the usage and one line naming the candidate columns and -c, checked before R runs (the test needs no R)'
  - a table with one numeric column besides the ID column ranks by it without -c, as before
  - the module JSON params record the resolved statistic column, ID column and direction (statcol, idcol, ascending; absent in 1.0.0); the schema is unchanged (params is an open object)
  - help's -c line, docs/tools/enrich.md and the skill's commands reference follow; CHANGELOG 1.0.1 notes the behaviour change (DETK-0600)
from: [DETK-0600]
scope: [de_toolkit/enrich.py, +tests/enrich/, +tests/cli/, +docs/tools/enrich.md, +skills/detk/references/commands.md, +CHANGELOG]
---

# fgsea needs -c when more than one column could rank

## Implementation plan

## Notes
