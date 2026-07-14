#
# de_toolkit (detk) container image
#
# Ubuntu base with R + Bioconductor (DESeq2, fgsea, logistf) and detk installed
# from the build context.
#

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# System packages: build tooling, R, and the dev headers R packages need.
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      curl \
      git \
      r-base \
      r-base-dev \
      libcurl4-openssl-dev \
      libxml2-dev \
      libssl-dev \
      python3 \
      python3-pip \
      python3-venv && \
    rm -rf /var/lib/apt/lists/*

# R / Bioconductor packages. biocLite was removed from Bioconductor in 2019;
# BiocManager is the supported installer.
RUN Rscript -e "install.packages('BiocManager', repos='https://cloud.r-project.org'); BiocManager::install(c('DESeq2','fgsea'), update=FALSE, ask=FALSE)" && \
    Rscript -e "install.packages('logistf', repos='https://cloud.r-project.org')"

ENV HOME=/root
WORKDIR /opt/de_toolkit

# Install detk from the build context (rather than re-cloning) for reproducible
# images that match the checked-out source.
COPY . /opt/de_toolkit
RUN pip install --no-cache-dir --break-system-packages .

WORKDIR /root
CMD ["bash"]
