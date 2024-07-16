#!/bin/bash --login

set -e

# conda create -n ovarian python=3.9 pip pandas joblib pyarrow rdkit mordredcommunity scikit-learn

# My packages
conda install -c conda-forge ipdb=0.13.11 --yes
conda install -c conda-forge python-lsp-server=1.2.4 --yes
