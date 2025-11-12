#!/bin/bash

flow=langgraph_chatbot_demo # use an available chatbot flow name

python -m athos.examples.chatbot_example --flow $flow
