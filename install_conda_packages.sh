conda install -c conda-forge -c bioconda python=3.5 docopt pandas pytest \
  future sphinx sphinx-autobuild patsy ipython statsmodels \
  ply matplotlib setuptools scipy scikit-learn mpld3 seaborn "rpy2>=2.7.3" \
  "icu=58.*"
conda install -c bioconda bioconductor-deseq2
conda list --export > conda_packages.txt
