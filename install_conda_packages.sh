conda install -c conda-forge -c bioconda python=3.5 docopt pandas pytest \
  future sphinx sphinx-autobuild patsy ipython statsmodels \
  ply matplotlib setuptools scipy scikit-learn "rpy2>=2.8.3"
conda list --export > conda_packages.txt
