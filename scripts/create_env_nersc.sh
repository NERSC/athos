#!/bin/bash

ml conda
conda create -n athos -y python=3.12
conda activate athos
pip install -e .[dev]
