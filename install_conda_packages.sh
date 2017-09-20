conda install -c conda-forge -c bioconda -c r python=3.5 docopt pandas pytest \
  "rpy2>=2.7.3" bioconductor-deseq2 future sphinx sphinx-autobuild patsy \
  pyparsing matplotlib setuptools scipy scikit-learn mpld3 seaborn
conda list --export > conda_packages.txt
