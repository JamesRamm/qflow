#!/bin/bash

# install redis
sudo apt-get update -q
sudo apt-get install redis-server

# install miniconda
wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh ;
chmod +x miniconda.sh && ./miniconda.sh -b
export PATH=$HOME/miniconda/bin:$PATH
conda update --yes conda

# install openmpi
sudo apt-get install -y libopenmpi-dev openmpi-bin;

# create conda environment for anuga
./create_anuga_env.sh

# create conda environment for qflow
conda create -n qflow python=3
source activate qflow
pip install -r requirements.txt
