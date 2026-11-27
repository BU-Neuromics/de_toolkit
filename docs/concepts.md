# Concepts & file formats

detk is built around two file types that every tool shares: the **counts
matrix file** and the **column data file** (also called the metadata or
covariates file). Both are plain character-delimited text; detk sniffs the
delimiter on input, and always writes comma-separated output.

The delimiter is sniffed from the first line (comma, tab, semicolon, pipe,
then space). A first line with none of them is a one-field header, as R's
`write.table` writes over row names (`"condition"` over `"S1","a"`); then
the delimiter is sniffed from the first data lines, which must all split on
it into the same number of fields. A one-field header over rows that split
unalike (`condition` over `S1,a` and `S2`) is an error, naming the file,
the delimiter and the first two lines whose field counts differ: quote a
field that holds the delimiter, or give every line the same fields. When no
data line has a delimiter either, the file is read as one column, such as a
list of IDs.

## The counts matrix file

Every tool accepts a counts matrix of the form:

| gene_id | sample_1 | sample_2 | ... | sample_m |
|---------|---------:|---------:|-----|---------:|
| gene_1  |    10000 |     1244 | ... |     2935 |
| gene_2  |     2023 |     1534 | ... |     1308 |
| gene_3  |        5 |        2 | ... |       19 |
| ...     |      ... |      ... | ... |      ... |
| gene_n  |        5 |        2 | ... |   150031 |

- The first column must contain unique gene or feature identifiers — Ensembl
  gene IDs, miRBase IDs, ChIP-seq peaks, genomic bins, anything.
- The remaining column names must be unique sample identifiers.
- The name of the first column doesn't matter; every row must have the same
  number of fields.

Every command that reads a counts matrix checks it as read, before the
column data selects or reorders any sample, and exits 1 (a bad input file,
see [Exit codes](#exit-codes)) naming the first offender and how many more
there are (DETK-0601, DETK-0830):

- **in every command**: a sample named more than once in the header, and a
  feature ID listed more than once. Positions are counted in the file, from
  1, among the samples and the features.
- **in the commands that need raw counts**: also a negative count, a sample
  with no numeric value, and a sample whose counts sum to 0 (zero depth).

| Needs raw counts (all four checks) | May take a normalized or transformed matrix (repeated IDs only) |
|---|---|
| `detk-norm` `deseq2`, `library`, `cpm`, `fpkm`, `tpm` | `detk-de firth` |
| `detk-de deseq2` | `detk-transform plog` |
| `detk-transform` `vst`, `rlog` | `detk-stats` (every subcommand) |
| | `detk-filter` |
| | `detk-outlier` `entropy`, `shrink` |

A normalized or log-transformed matrix may hold negative values or a column
of zeros, so the commands on the right accept them. The commands on the left
model or scale counts, which a negative value or an empty sample would make
wrong without a word.

## The column data file

Tools that need per-sample information (differential expression, PCA
coloring, group-wise filtering) take a column data file:

| sample_names | condition | sex | ... | covariate_p |
|--------------|-----------|-----|-----|-------------|
| sample_1     | case      | M   | ... | c1          |
| sample_2     | control   | F   | ... | c9          |
| ...          | ...       | ... | ... | ...         |
| sample_m     | case      | F   | ... | c3          |

The first column holds sample names matching the column names of the counts
file; remaining columns hold any covariates needed for analysis. detk matches
samples up by name, but it is good practice to keep the order consistent —
tools accept a `--strict` flag to require it. The
[`detk-util tidy`](tools/util.md) commands subset and reorder the two files
against each other.

## Design formulas

Tools that fit models (`detk-de`, non-blind `detk-transform rlog`) take a
design formula written in detk's [formula mini-language](formulas.md), which
resolves column data columns into a full-rank model matrix with
machine-friendly column names like `Status__case`.

## The report layer

Every tool invocation (unless `--no-report` is passed) drops a JSON document
describing its parameters and results into `detk_report/json/`. The
[`detk-report`](report.md) tool renders all accumulated documents into a
single self-contained HTML report. The JSON documents are stable,
machine-readable provenance — you can consume them directly in downstream
tooling.

## Exit codes

Every detk command exits with one of three codes (DETK-0031), which its
`--help` also states:

| Code | Meaning |
|-----:|---------|
| 0 | success (and `--help`, `--version`) |
| 2 | usage error: the command line is wrong, such as an unknown option, a missing argument, a bad option value or an invalid design formula; the usage is printed with the error |
| 1 | any other failure: a bad input file, a missing R or R package, a step that fails |

A failure prints one line on stderr, `<command>: error: <cause>`; with
`--verbose` the traceback is printed before it. A script can tell a mistake
in its own command line (2) from a problem with the data or the environment
(1).

## Shell completion

detk ships completion scripts for bash, zsh and tcsh (DETK-0032), which
complete every detk command (`detk` and each `detk-<command>`), its
subcommands, options and choices, and file names where an argument takes a
file. `detk completion <shell>` prints the script; load it from your shell's
startup file:

```console
# bash, in ~/.bashrc
eval "$(detk completion bash)"

# zsh, in ~/.zshrc, after compinit
eval "$(detk completion zsh)"

# tcsh: write the script once, then source it in ~/.tcshrc
detk completion tcsh > ~/.detk.tcsh
source ~/.detk.tcsh
```

The scripts are part of the installed package, so printing one needs
nothing else installed. Open a new shell (or source the startup file) for
the completion to take effect.
