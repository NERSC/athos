#!/bin/bash

ml conda
conda create -n athos -y python=3.12
conda activate athos
pip install -e .[dev]

# Install jupyter kernel for running notebooks
python -m ipykernel install --user --name athos
