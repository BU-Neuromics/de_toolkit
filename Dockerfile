#
# Ubuntu Dockerfile
#
# https://github.com/dockerfile/ubuntu
#

# Pull base image.
FROM ubuntu:18.04

# Install.
RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y build-essential && \
  apt-get install -y software-properties-common && \
  apt-get install -y byobu curl git htop man unzip wget && \
  rm -rf /var/lib/apt/lists/*

ARG DEBIAN_FRONTEND=noninteractive
# install R
RUN \
  apt update -q && \
  echo "America/New_York" > /etc/timezone && \
  echo 12 | apt-get -qy install r-base r-base-dev libcurl4-openssl-dev libxml2-dev

RUN Rscript -e "source('http://bioconductor.org/biocLite.R'); biocLite(c('DESeq2','fgsea'))"
RUN Rscript -e "install.packages('logistf')"

# install python 3 things
RUN \
  apt-get -y install python3 python3-pip python3-dev && \
  pip3 install --upgrade pip setuptools && \
  rm $(which pip) && \
  ln -s $(which pip3) /usr/bin/pip

# Add files.
#ADD root/.bashrc /root/.bashrc
#ADD root/.gitconfig /root/.gitconfig
#ADD root/.scripts /root/.scripts

# Set environment variables.
ENV HOME /root

# Define working directory.
WORKDIR /root

# install current detk
RUN \
    git clone https://bitbucket.org/bubioinformaticshub/de_toolkit.git && \
    cd de_toolkit && \
    pip3 install -r requirements.txt && \
    python3 setup.py install

# Define default command.
CMD ["bash"]
