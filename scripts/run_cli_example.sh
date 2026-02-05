#!/bin/bash

export ATHOS_LOG_LEVEL=DEBUG
python -m athos.main \
    --config config/config.yaml \
    --flow lang_chat \
    --input "what is NERSC?"
