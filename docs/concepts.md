# Concepts & file formats

detk is built around two file types that every tool shares: the **counts
matrix file** and the **column data file** (also called the metadata or
covariates file). Both are plain character-delimited text; detk sniffs the
delimiter on input, and always writes comma-separated output.

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
