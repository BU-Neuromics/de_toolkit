# detk command reference

The usage of each command the `detk` skill uses, copied from the commands'
own `--help` output (de_toolkit's test suite checks that they still match).
`<command> <subcommand> --help` prints the usage of the installed version.

Every command also accepts the common options:

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

Most commands write their table to stdout unless given `-o FILE`, and log to
stderr. Each run also writes a JSON document under `<report-dir>/json/`
unless `--no-report` is given.

## `detk-stats summary`

```text
Usage:
    detk-stats summary [options] <counts_fn> [<cov_fn>]

Options:
    --column-data=FN       DEPRECATED: pass cov_fn as positional command line
                           argument instead
    --color-col=COLNAME    Use column data column COLNAME for coloring output plots
    --bins=BINS            Number of bins to use for the calculated
                           distributions [default: 20]
    --log                  log transform count statistics
    --density              Produce density distribution by dividing each distribution
                           by the appropriate sum
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
```

## `detk-filter`

```text
Usage:
    detk-filter [options] <command> <counts_fn> [<cov_fn>]

Options:
    -o <out_fn> --output=<out_fn>    Name of output file [default: stdout]
    --column-data=<column_data_fn>   DEPRECATED: pass cov_fn as positional
                                     command line argument instead
```

## `detk-util gather`

```text
Usage:
    detk-util gather [options] <files>...

Options:
    --format=FMT           salmon, kallisto, htseq, featurecounts or auto
                           [default: auto]
    --column=COL           Column to extract from each file, by name or 0-based
                           position (default: the format's count column)
    --name-from=REGEX      Regular expression deriving each sample name from
                           its file path (the first group, or the whole match)
    --on-mismatch=WHAT     What to do when the samples list different features:
                           error, fill (with 0) or drop [default: error]
    -o FILE --output=FILE  Destination of the counts matrix [default: stdout]
```

## `detk-util tidy`

```text
Usage:
    detk-util tidy [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
    -p FILE --column-data-output=FILE  Destination of tidied column data
```

## `detk-norm deseq2`

```text
Usage:
    detk-norm deseq2 [options] <counts_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
    --size-factors=FILE          Write out the size factors found by the DESeq2
                                 method to two column tab separated file where
                                 the first column is sample name and the second
                                 column is the size factor
```

## `detk-norm fpkm`

```text
Usage:
    detk-norm fpkm [options] <counts_fn> <lengths_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
```

## `detk-norm library`

```text
Usage:
    detk-norm library [options] <counts_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
```

## `detk-norm cpm`

```text
Usage:
    detk-norm cpm [options] <counts_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
```

## `detk-norm tpm`

```text
Usage:
    detk-norm tpm [options] <counts_fn> <lengths_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
```

## `detk-transform vst`

```text
Usage:
    detk-transform vst [options] <counts_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
```

## `detk-outlier entropy`

```text
Usage:
    detk-outlier entropy <counts_fn> [options]

Options:
    -p P --percentile=P    Float value between 0 and 1
    -o FILE --output=FILE  Name of the ouput csv
    --plot-output=FILE     Name of the plot png
```

## `detk-de deseq2`

```text
Usage:
    detk-de deseq2 [options] <design> <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --routput-dir=DIR      Path to output directory for R stuffs, useful for
                           debuggin out
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
    --norm-counts          Prevent DESeq2 from normalizing counts prior to
                           running differential expression, default behavior
                           assumes that provided counts are raw
    --last-term-only       Use the default DESeq2 behavior of returning DE parameters
                           for the last term in the model, default behavior is to
                           report parameters for all variables in the model
    --gene-wise-disp       Use estimateDispersionsGeneEst instead of estimateDispersions
    --cores=N              Tell DESeq2 to use N cores when running, requires the
                           BiocParallel Bioconductor package to be installed [default: none]
```

## `detk-de firth`

```text
Usage:
    detk-de firth [options] <design> <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --routput-dir=DIR      Path to output directory for R stuffs, useful for
                           debuggin out
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
    --standardize          Standardize counts prior to running logistic regression
                           as to obtain standardized (i.e. directly comparable)
                           beta coefficients
    --cores=N              Tell R to use N cores when running, requires the
                           parallel R package to be installed [default: none]
```

## `detk-enrich fgsea`

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
    --routput-dir=DIR         Path to output directory for R stuffs, useful for
                              debuggin out
    --rda=FILE                write out the fgsea result to the provide file
                              using saveRDS() in R
```

## `detk-util annotate`

```text
Usage:
    detk-util annotate [options] <result_fn> <mapping_fn>

Options:
    -i FIELD --idcol=FIELD  Column in the result file holding the feature IDs to
                            join on [default: 0]
    --map-from=COL          Column in the mapping file matching the result IDs
                            [default: 0]
    --map-to=COLS           Comma-separated mapping columns to add, or 'all' for
                            every column but --map-from [default: all]
    --strip-versions        Strip trailing .N version suffixes from Ensembl-style
                            IDs on both sides before joining
    --drop-unmapped         Drop result rows with no mapping instead of leaving
                            their added columns empty
    -o FILE --output=FILE   Destination of the annotated table [default: stdout]
```

## `detk-report generate`

```text
Usage:
    detk-report generate [options]

Options:
    --dev  Pretty-print the embedded JSON payload (larger file, easier to read)
```

## `detk-report clean`

```text
Usage:
    detk-report clean [options]
```

## `detk-wrapr check`

```text
Usage:
    detk-wrapr check [options]
    detk-wrapr run [options] <rscript> [<counts_in>] [<out>]

Options:
    --rpath=PATH        Path to Rscript executable, inferred from the environment
                        by default
    --routput-dir=PATH  A directory name to write all of the relevant files to
                        when running this wrapr, useful for debugging an R
                        script if things go wrong, by default the directory
                        and files created are temporary and deleted after
                        execution
    --meta-in=PATH      Path to metadata file corresponding to columns in counts,
                        same as is passed to other detk functions
    --meta-out=PATH     Path to metadata file corresponding to columns in counts,
                        same as is passed to other detk functions
    --params-in=PATH    Path to JSON formatted file containing parameters needed
                        by R script
    --params-out=PATH   Path to JSON formatted file to be created with output
                        from the R script
    --strict            Ensure counts column names and the first row of the
                        metadata file provided (if any) match, otherwise fail
```
