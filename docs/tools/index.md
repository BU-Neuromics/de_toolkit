# Tools overview

detk is organized into modules, each exposed both as a subcommand of `detk`
and as a standalone executable (`detk stats ...` ≡ `detk-stats ...`):

| Tool | Purpose | Needs R |
|------|---------|---------|
| [`detk-stats`](stats.md) | count matrix statistics (distributions, zeros, entropy, PCA) | no |
| [`detk-filter`](filter.md) | filter features with a mini-language | no |
| [`detk-norm`](norm.md) | DESeq2 / library-size / FPKM normalization | no |
| [`detk-transform`](transform.md) | plog / rlog / VST transformations | rlog, vst |
| [`detk-de`](de.md) | DESeq2 and Firth logistic differential expression | yes |
| [`detk-enrich`](enrich.md) | fgsea pre-ranked gene set enrichment | yes |
| [`detk-outlier`](outlier.md) | outlier count identification and shrinkage | no |
| [`detk-util`](util.md) | tidy counts/column-data files against each other | no |
| [`detk-wrapr`](wrapr.md) | run custom R scripts through the detk R bridge | yes |
| [`detk-report`](../report.md) | render accumulated results into an HTML report | no |

## Common options

Every subcommand accepts these options in addition to its own:

```text
Common options:
    -d CHAR --out-delim=CHAR  Delimiter to use for output file [default: ,]
    --report-dir=DIR          Specify the report directory [default: ./detk_report]
    --no-report               Do not generate the HTML report
    --version                 Print out detk version and exit
    -v --verbose              Make log output verbose
    -q --quiet                Turn off all logging except warnings and errors
    --shut-up                 Turn off ALL logging
```

Most tools write their primary output to stdout by default and accept
`-o FILE`/`--output=FILE` to write to a file instead. Unless `--no-report` is
given, each invocation also records a JSON document under
`<report-dir>/json/` for the [report](../report.md).
