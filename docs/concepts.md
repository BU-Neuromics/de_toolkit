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
file; remaining columns hold any covariates needed for analysis. The two
files must name the same samples: a sample in only one of them is an error
(exit 1) that names it, rather than a silent subset (DETK-0600). detk matches
the samples up by name, so the column data rows may come in any order, but
it is good practice to keep the order consistent — tools accept a `--strict`
flag to require it. To analyse only some of the samples, subset the files
explicitly with the [`detk-util tidy`](tools/util.md) commands, which keep
the samples in both and reorder the column data to the counts.

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
