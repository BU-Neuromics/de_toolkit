# detk command reference

The usage of each command the `detk` skill uses, copied from the commands'
own `--help` output (de_toolkit's test suite checks that they still match).
`<command> <subcommand> --help` prints the full help of the installed
version: description, usage, arguments, options, common options and
examples.

Every command also accepts the common options:

```text
common options:
  -d, --out-delim CHAR  Delimiter to use for the output file (default: ,)
  --report-dir DIR      Directory to write the HTML report and module JSON into
                        (default: ./detk_report)
  --no-report           Do not write the HTML report
  --version             Print the detk version and exit
  -v, --verbose         Make log output verbose
  -q, --quiet           Turn off all logging except warnings and errors
  --shut-up             Turn off ALL logging
```

Every command exits 0 on success, 2 on a usage error (the command line is
wrong: fix it from the usage and `--help`) and 1 on any other failure (bad
input, a missing R or R package, a failing step). A failure's cause is the
last line on stderr, `<command>: error: <cause>`; `--verbose` adds the
traceback above it.

Most commands write their table to stdout unless given `-o FILE`, and log to
stderr. Each run also writes a JSON document under `<report-dir>/json/`
unless `--no-report` is given.

## `detk-stats summary`

```text
usage: detk-stats summary [options] <counts_fn> [<cov_fn>]

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Column data file: samples in rows, covariates in columns

options:
  -h, --help         Print this help and exit
  --color-col COL    Column of the column data to color the output plots by
  --bins N           Number of bins of the calculated distributions
                     (default: 20)
  --log              log10 transform the counts first (zeros are left out)
  --density          Report each distribution as a density, divided by its sum
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `detk-filter`

```text
usage: detk-filter [options] <command> <counts_fn> [<cov_fn>]

positional arguments:
  <command>    Filter expression: the rows to keep, quoted
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Column data file: samples in rows, covariates in columns, for
               group filters

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Name of the output file (default: stdout)
```

## `detk-util gather`

```text
usage: detk-util gather [options] <files>...

positional arguments:
  <files>  Quantifier output files, one per sample (a quoted glob is expanded)

options:
  -h, --help          Print this help and exit
  --format FMT        Format of the files; auto detects it from each file's
                      header (choices: salmon, kallisto, htseq, featurecounts,
                      auto) (default: auto)
  --column COL        Column to extract from each file, by name or 0-based
                      position (without it: the format's count column)
  --name-from REGEX   Regular expression deriving each sample name from its file
                      path (the first group, or the whole match)
  --on-mismatch WHAT  What to do when the samples list different features: stop
                      with an error, fill with 0 or drop them (choices: error,
                      fill, drop) (default: error)
  -o, --output FILE   Destination of the counts matrix (default: stdout)
```

## `detk-util tidy`

```text
usage: detk-util tidy [options] <counts_fn> <cov_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Sample information file: samples in rows, delimited

options:
  -h, --help                  Print this help and exit
  -o, --output FILE           Destination of tidied counts data
                              (default: stdout)
  -p, --column-data-output FILE
                              Destination of tidied column data (not written
                              without it)
```

## `detk-norm deseq2`

```text
usage: detk-norm deseq2 [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help           Print this help and exit
  -o, --output FILE    Destination of normalized output in CSV format
                       (default: stdout)
  --size-factors FILE  Write out the size factors found by the DESeq2 method to
                       a two column tab separated file: a header line 'sample',
                       'size_factor', then one line per sample of its name and
                       size factor
```

## `detk-norm fpkm`

```text
usage: detk-norm fpkm [options] <counts_fn> <lengths_fn>

positional arguments:
  <counts_fn>   Counts file: features in rows, samples in columns, delimited
  <lengths_fn>  Feature lengths file: feature name and length in bases

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of normalized output in CSV format
                     (default: stdout)
```

## `detk-norm library`

```text
usage: detk-norm library [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of normalized output in CSV format
                     (default: stdout)
```

## `detk-norm cpm`

```text
usage: detk-norm cpm [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of normalized output in CSV format
                     (default: stdout)
```

## `detk-norm tpm`

```text
usage: detk-norm tpm [options] <counts_fn> <lengths_fn>

positional arguments:
  <counts_fn>   Counts file: features in rows, samples in columns, delimited
  <lengths_fn>  Feature lengths file: feature name and length in bases

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of normalized output in CSV format
                     (default: stdout)
```

## `detk-transform vst`

```text
usage: detk-transform vst [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of the transformed counts in CSV format
                     (default: stdout)
  --rda FILE         Write the R result objects of the analysis to FILE with
                     saveRDS()
```

## `detk-outlier entropy`

```text
usage: detk-outlier entropy [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help          Print this help and exit
  -p, --percentile N  The entropy percentile below which a feature is flagged,
                      between 0 and 1
  -o, --output FILE   Destination of the entropy and flag of each feature in CSV
                      format
  --plot-output FILE  Destination of a PNG plot of the entropy distribution and
                      threshold
```

## `detk-de deseq2`

```text
usage: detk-de deseq2 [options] <design> <counts_fn> <cov_fn>

positional arguments:
  <design>     Model formula, quoted, such as "counts ~ group"
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Sample information file: samples in rows, the first column their
               names

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  --routput-dir DIR  Directory to keep the R script, its inputs and outputs in,
                     for debugging
  --rda FILE         File to saveRDS() the R result objects of the analysis to
  --strict           Require the counts file's sample columns to be the same as,
                     and in the same order as, the rows of the sample
                     information file
  --norm-counts      Do not let DESeq2 normalize the counts: they are already
                     normalized
  --last-term-only   Report the parameters of the model's last term only
                     (DESeq2's default)
  --gene-wise-disp   Use estimateDispersionsGeneEst instead of
                     estimateDispersions
  --cores N          Number of cores DESeq2 uses (needs the BiocParallel
                     package) (default: none)
```

## `detk-de firth`

```text
usage: detk-de firth [options] <design> <counts_fn> <cov_fn>

positional arguments:
  <design>     Model formula, quoted, such as "counts ~ group"
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Sample information file: samples in rows, the first column their
               names

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  --routput-dir DIR  Directory to keep the R script, its inputs and outputs in,
                     for debugging
  --rda FILE         File to saveRDS() the R result objects of the analysis to
  --strict           Require the counts file's sample columns to be the same as,
                     and in the same order as, the rows of the sample
                     information file
  --standardize      Standardize the counts first, so the coefficients are
                     directly comparable
  --cores N          Number of cores R uses (needs the parallel R package)
                     (default: none)
```

## `detk-enrich fgsea`

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
                        the last numeric column if not given
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

## `detk-util annotate`

```text
usage: detk-util annotate [options] <result_fn> <mapping_fn>

positional arguments:
  <result_fn>   Result table to annotate, e.g. the output of detk-de
  <mapping_fn>  Mapping table: feature IDs and the metadata columns to add

options:
  -h, --help         Print this help and exit
  -i, --idcol COL    Column in the result file holding the feature IDs to join
                     on (default: 0)
  --map-from COL     Column in the mapping file matching the result IDs
                     (default: 0)
  --map-to COLS      Comma-separated mapping columns to add, or 'all' for every
                     column but --map-from (default: all)
  --strip-versions   Strip trailing .N version suffixes from Ensembl-style IDs
                     before joining
  --drop-unmapped    Drop result rows with no mapping instead of leaving their
                     added columns empty
  -o, --output FILE  Destination of the annotated table (default: stdout)
```

## `detk-report generate`

```text
usage: detk-report generate [options]

options:
  -h, --help  Print this help and exit
  --dev       Pretty-print the embedded JSON payload (larger file, easier to
              read)
```

## `detk-report clean`

```text
usage: detk-report clean [options]

options:
  -h, --help  Print this help and exit
```

## `detk-wrapr check`

```text
usage: detk-wrapr check [options]

options:
  -h, --help         Print this help and exit
  --rpath FILE       Path to the Rscript executable; found on the PATH when not
                     given
  --routput-dir DIR  Keep the files handed to and written by R in DIR, for
                     debugging (when not given, a temporary directory deleted
                     after the run)
  --meta-in FILE     Sample information file for the columns of the counts, as
                     other detk commands take it
  --meta-out FILE    Destination of the sample information as the R script
                     leaves it
  --params-in FILE   JSON file of parameters handed to the R script
  --params-out FILE  Destination of the JSON output parameters of the R script
  --strict           Require the counts columns and the --meta-in rows to match
```
