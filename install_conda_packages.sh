# r-nloptr is needed by logistf but fails on install from CRAN
# install here
conda install -c r -c bioconda -c conda-forge python=3.6 r-base r-nloptr \
    bioconductor-deseq2 bioconductor-genomeinfodbdata r-logistf bioconductor-fgsea
# GenomeInfoDb appears to be broken in conda
R -e 'source("http://bioconductor.org/biocLite.R"); biocLite("GenomeInfoDb")'
pip install -r requirements.txt
conda list --export > conda_packages.txt
