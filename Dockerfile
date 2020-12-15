FROM ubuntu:18.04

## Seting env and updating required system packages
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
RUN apt-get update
RUN apt-get install -y wget && rm -rf /var/lib/apt/lists/*

## Install miniconda
RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh

## Install Pyntacle
RUN conda install python=3.7
RUN conda install -y -c conda-forge -c bfxcss pyntacle=1.3.2

MAINTAINER Tommaso Mazza (IRCCS Casa Sollievo della Sofferenza) <bioinformatics@css-mendel.it>

## Setting the entrypoint
ENTRYPOINT ["/root/miniconda3/bin/pyntacle"]
CMD [ ]
