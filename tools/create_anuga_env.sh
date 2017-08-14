#!/bin/bash
conda create -n anuga python=2
source activate anuga
apt-get update
apt-get install -y gcc gfortran
gcc -v
conda install -y nomkl nose numpy scipy matplotlib netcdf4
conda install -y -c pingucarsti gdal
git clone https://github.com/GeoscienceAustralia/anuga_core.git
cd anuga_core/
python setup.py build
python setup.py install
source deactivate
