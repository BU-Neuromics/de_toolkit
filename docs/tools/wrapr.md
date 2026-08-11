# `wrapr` — thin wrapper for running R scripts

Thin wrapper interface for running R scripts from detk. This is a replacement
for [rpy2], a heavy dependency fraught with danger and hardship.

[rpy2]: https://rpy2.github.io/

!!! note

    This module is mostly intended for internal use by detk when interacting
    with R. A CLI interface is provided because why not, but is only intended
    for advanced cases where you want to command-line-ize an R script that
    fits the interface. If you have a one-off R script that needs to be
    integrated into your workflow, it would probably be better to just run it
    with R. Caveat emptor.

## Setup

`wrapr` assumes R and any necessary packages are already installed. With
conda/mamba:

```bash
mamba install -c conda-forge r-base r-jsonlite
```

The [jsonlite] R package is required. Verify your environment:

```console
$ detk wrapr check
R found: True
R path: /usr/bin/Rscript
jsonlite found: True
```

[jsonlite]: https://cran.r-project.org/package=jsonlite

## The interface

`wrapr` implements a well-defined interface between detk and R through a
bridge script. From the command line:

```bash
detk-wrapr run \
  --meta-in=/path/to/metadata \        # metadata filename corresponding to input counts
  --meta-out=/path/to/metadata_out \   # where modified metadata should be written
  --params-in=/path/to/params.json \   # JSON file with parameters needed by R
  --params-out=/path/to/params_out.json \  # where R can pass parameters back out
  /path/to/rscript \                   # R script written to use the interface
  /path/to/input_counts \              # counts matrix
  /path/to/output                      # where tabular output should be written
```

Arguments starting with `--` are optional. Input metadata and counts should be
tabular as accepted elsewhere by detk. The input parameters file should be
JSON containing an object whose fields map directly to R `list` members.

The bridge script makes the following variables available in the R environment
where the script runs:

- **`counts.fn`** — path to the counts file provided to `detk-wrapr`
- **`out.fn`** — path where new counts should be written after R has operated
  on them, e.g. `write.csv(counts.mat, out.fn)`
- **`params`** — an R `list` containing the values from the parameter JSON
  file

## Example

Say we want an R script that adds a configurable pseudocount to every count.
Write the parameter file:

```json
{
  "pseudocount": 1
}
```

and the script `pseudocount.R`:

```r
# counts.fn, params, and out.fn are already defined
mat <- read.csv(counts.fn, rownames=1, colnames=1)
new.mat <- mat + params$pseudocount
write.csv(new.mat, out.fn)
```

then run:

```bash
detk wrapr run --params-in=pseudocount_params.json \
  pseudocount.R counts.csv counts_plus_pseudo.csv
```

`counts_plus_pseudo.csv` will contain the result. See the
[API reference](../api.md) for the `WrapR` class used internally.
