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
  `cond__log2FoldChange`

```bash
detk-enrich fgsea -o gsea_results.csv -i gene -c cond__log2FoldChange msigdb_c2cp.gmt deseq2_results.csv
```

```text
Usage:
    detk-enrich fgsea [options] <gmt_fn> <result_fn>

Options:
    -o FILE --output=FILE     Destination of fgsea output [default: stdout]
    -p PROCS --cores=PROCS    Ask BiocParallel to use PROCS processes when
                              executing fgsea in parallel, requires the
                              BiocParallel package to be installed
    -i FIELD --idcol=FIELD    Column name or 0-based integer index to use as
                              the gene identifier [default: 0]
    -c FIELD --statcol=FIELD  Column name or 0-based integer index to use as
                              the statistic for ranking, defaults to the last
                              numeric column in the file
    -a --ascending            Sort column ascending, default is to sort
                              descending, use this if you are sorting by p-value
                              or want to reverse the directionality of the NES
                              scores
    --abs                     Take the absolute value of the column before
                              passing to fgsea
    --filter-unannotated      Remove any genes from the result matrix that have
                              identifiers that don't exist in any gene set of
                              the GMT
    --minSize=INT             minSize argument to fgsea [default: 15]
    --maxSize=INT             maxSize argument to fgsea [default: 500]
    --nperm=INT               nperm argument to fgsea [default: 10000]
    --multilevel              Use the fgseaMultilevel function, instead of fgsea
    --rda=FILE                write out the fgsea result to the provide file
                              using saveRDS() in R
```

[fgsea]: https://bioconductor.org/packages/release/bioc/html/fgsea.html
