``wrapr`` - Thin wrapper for running R scripts
==============================================

Thin wrapper interface for running R scripts from detk. This is a replacement
for rpy2_, which is a heavy dependency fraught with danger and hardship.

.. _rpy2: https://rpy2.bitbucket.io

.. note::

   This module is mostly intended for internal use by detk when interacting
   with R. A CLI interface is provided because why not, but is only intended
   to be used in advanced cases when you want to commandline-ize an R script
   that fits into the interface. If you have a one-off R script that needs to
   be integrated into your workflow, it would probably be better to just write
   it in R. Caveat emptor.

Setup
-----

The ``wrapr`` interface assumes that R and any necessary packages have been
already installed by the user. If you are using conda_, you can install R
easily with::

  $ conda install -c r r-base

.. _conda: https://conda.io/miniconda.html

Once installed, ``wrapr`` also requires the jsonlite_ R package to be
installed::

  $ R
  > install.packages("jsonlite")

.. _jsonlite: https://cran.r-project.org/web/packages/jsonlite/index.html

To verify that your environment is properly set up to use ``wrapr``, run::

  $ detk wrapr check
  R found: True
  R path: /usr/bin/Rscript
  jsonlite found: True

The interface
-------------

``wrapr`` implements a well-defined interface between detk and R through a
bridge script. From the command line, the following inputs are possible::

  $ detk-wrapr run \
    --meta-in=/path/to/metadata \ # metadata filename corresponding to input counts
    --meta-out=/path/to/metadata_out \ # filename where modified metadata should be written
    --params-in=/path/to/params.json \ # JSON formatted file with parameters needed by R
    --params-out=/path/to/output_params.json \ # filename where parameters/values can be passed back out of R
    /path/to/rscript \ # R script written to use the interface
    /path/to/input_counts \ # counts matrix
    /path/to/output \ # filename where tabular output should be written

Arguments starting with ``--`` are optional. Input metadata and counts should
be tabular as accepted elsewhere by detk. The input parameters file should be
JSON formatted, containing an object with fields that are mapped directly to
R ``list`` members.

The bridge script makes the following variables available
in the R environment where the R script is run:

- **counts.fn**: path to the counts filename provided to ``detk-wrapr``
- **out.fn**: path to the file where new counts will be written after
  R has operated on them, the user is expected to write to this file e.g.
  ``write.csv(counts.mat, counts.out.fn)``
- **params**: an R ``list`` that contains parameter values as included in
  the parameter JSON file

For example, say we wanted to write an R script that added a configurable
pseudocount to every count in a counts matrix. We could write the JSON
parameter file as follows::

  {
    "pseudocount": 1
  }

And write the following R script, named ``pseudocount.R``::

  # counts.fn, params, and out.fn are already defined
  mat <- read.csv(counts.fn,rownames=1,colnames=1)
  new.mat <- mat + params$pseudocount
  write.csv(new.mat,out.fn)

The command to execute this wrapr code might be::

  $ detk wrapr run --params-in=pseudocount_params.json \
  pseudocount.R counts.csv counts_plus_pseudo.csv

The file ``counts_plus_pseudo.csv`` will contain the result of the R script
operation.

API documentation
-----------------

.. autoclass:: de_toolkit.wrapr.WrapR
    :members:

.. autofunction:: de_toolkit.wrapr.wrapr

.. autofunction:: de_toolkit.wrapr.get_r_path

.. autofunction:: de_toolkit.wrapr.check_r

.. autofunction:: de_toolkit.wrapr.check_r_package
