# r-nloptr is needed by logistf but fails on install from CRAN
# install here
conda install -c r -c bioconda python=3.6 r-base r-nloptr
pip install -r requirements.txt
conda list --export > conda_packages.txt
Rscript install_r_packages.R
