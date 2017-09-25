.. de_toolkit documentation master file, created by
   sphinx-quickstart on Tue May  2 18:07:57 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to de_toolkit's documentation!
======================================

Introduction
------------

``de_toolkit`` is a suite of Bioinformatics tools useful in differential
expression analysis and other high-throughput sequencing count-based workflows.
The tools are implemented either through direct implementation in python or as
a convenience wrapper around R packages using rpy2_.

The toolkit is both a python module and a command line interface that wraps
primary module functions to facilitate easy integration into workflows. For
instance, to perform DESeq2_ normalization of a counts matrix contained in the
file ``counts_matrix.tsv``, you could run on the command line:

.. code-block:: bash

  detk-norm deseq counts_matrix.tsv > norm_counts_matrix.tsv

The counts in the counts matrix file will be normalized using the DESeq2 method
and output to the ``norm_counts_matrix.tsv`` file as the equivalent of:

.. code-block:: R

  library(DESeq2)

  # TODO: add actual equivalent code

Module Documentation
--------------------

.. toctree::
   :maxdepth: 2

   norm
   de
   patsy_lite
   outlier
   transform
   filter
   stats

The following functionality is (or will be) implemented by the package (items
in italics are not yet implemented):

* :doc:`norm`
    - DESeq2
    - *trimmed mean*
    - *reference norm*
    - library size
    - *FPKM*
    - *user supplied*
* :doc:`de`
    - *DESeq2*
    - Firth's Logistic Regression
    - *t-test*
* :doc:`outlier`
    - *entropy*
    - *Cook's distance*
* :doc:`transform`
    - DESeq2 Variance Stabilizing Transform
    - *RUVSeq transformation*
    - *trim*
    - *shrink*
* :doc:`filter`
    - *nonzero*
    - *mean*
* :doc:`stats`
    - *summary*
    - *dist*
    - *PCA*

Installing
----------

conda package
+++++++++++++

We suggest installing this package using anaconda_ on the bubhub channel:

.. code-block:: bash

  conda install -c bubhub de_toolkit

Manual installation
+++++++++++++++++++

If conda is not available, ensure the following packages are installed and
available in your environment:

* python packages (python>=3.5)
    - docopt
    - pandas
    - numpy
* R packages (R>=3.2)
    - R>=3.2
    - docopt

The following packages are only required to use the corresponding submodule
functions:

* R packages
    - DESeq2 (bioconductor)
    - RUVSeq (bioconductor)
    - logistf (CRAN)

We suggest using anaconda_ to create an environment that contains the software
necessary, e.g.:

.. code-block:: bash

  conda create -n de_toolkit python=3.5

  ./install_conda_packages.sh

  # if you want to use the R functions (Firth, DESeq2, etc.)
  Rscript install_r_packages.sh 

In development, when you want to run the toolkit, use the ``setup.py`` script:

.. code-block:: bash

  python setup.py install

This should make the ``detk`` and its subtools available on the command line. Whenever you make changes
to the code you will need to run this command again.


.. _rpy2: https://rpy2.readthedocs.io/
.. _DESeq2: http://bioconductor.org/packages/release/bioc/html/DESeq2.html
.. _anaconda: http://anaconda.org

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
