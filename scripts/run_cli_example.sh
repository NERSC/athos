#!/bin/bash

python -m athos.main \
    --config config/config.yaml \
    --flow langgraph_chatbot_demo \
    --input "what is NERSC?"
