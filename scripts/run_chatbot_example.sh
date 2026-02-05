#!/bin/bash

flow=lang_chat # use an available chatbot flow name
export ATHOS_LOG_LEVEL=DEBUG

python -m athos.examples.chatbot_example --flow $flow
