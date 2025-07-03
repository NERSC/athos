#!/bin/bash

python -m athos.main \
    --config config/config.yaml \
    --flow hpc_chatbot \
    --log-level INFO \
    --input "what is NERSC?"
