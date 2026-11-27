# `enrich` — set enrichment methods

Statistical set enrichment methods, currently pre-ranked Gene Set Enrichment
Analysis via the [fgsea] Bioconductor package (requires R).

## `fgsea`

Perform pre-ranked GSEA on a differential expression (or any) result file
against a GMT gene set file.

The GMT file must be tab delimited with the set name in the first column, a
description in the second (ignored by detk), and one feature ID per column
after that — one feature set per line. The result file can be any character
delimited file with column names in the first row.

The feature IDs must come from the same identifier system (gene symbols,
ENSGIDs, ...) in both files. You will likely need to provide:

- `-i <col>` — column in the results file containing feature IDs
- `-c <col>` — column containing the ranking statistic, e.g.
  `cond__treated__log2FoldChange`, the log fold change of the `treated`
  level of `cond`, as `detk-de deseq2` names it

`-c` is required whenever the results have more than one numeric column
besides the ID column (counted after `-i`), as every `detk-de` result does:
without it, `detk-enrich fgsea` exits 2 with a line naming the candidate
columns, before R runs. A table with one numeric column besides the ID
column ranks by it without `-c`. The module JSON records the ranking used in
its params: `statcol`, `idcol` and `ascending`. (In 1.0.0, without `-c`,
fgsea ranked silently by the last numeric column, which in a DESeq2 result
is an adjusted p-value.)

```bash
detk-enrich fgsea -o gsea_results.csv -i gene -c cond__treated__log2FoldChange msigdb_c2cp.gmt deseq2_results.csv
```

```text
usage: detk-enrich fgsea [options] <gmt_fn> <result_fn>

positional arguments:
  <gmt_fn>     Gene sets in GMT format: name, description, IDs
  <result_fn>  Delimited result file with column names, such as a detk-de result

options:
  -h, --help            Print this help and exit
  -o, --output FILE     Destination of fgsea output (default: stdout)
  -p, --cores N         Number of processes fgsea uses (needs the BiocParallel
                        package)
  -i, --idcol COL       Column (name or 0-based index) holding the feature IDs
                        (default: 0)
  -c, --statcol COL     Column (name or 0-based index) of the ranking statistic;
                        required when the results have more than one numeric
                        column besides the ID column
  -a, --ascending       Rank ascending (for p-values, or to reverse the sign of
                        NES)
  --abs                 Rank by the absolute value of the statistic
  --filter-unannotated  Drop the features whose IDs are in no gene set of the
                        GMT
  --minSize N           minSize argument to fgsea (default: 15)
  --maxSize N           maxSize argument to fgsea (default: 500)
  --nperm N             nperm argument to fgsea (default: 10000)
  --multilevel          Use the fgseaMultilevel function, not fgsea
  --routput-dir DIR     Directory to keep the R script, its inputs and outputs
                        in, for debugging
  --rda FILE            File to saveRDS() the fgsea result to
```

[fgsea]: https://bioconductor.org/packages/release/bioc/html/fgsea.html
