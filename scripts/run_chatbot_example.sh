#!/bin/bash

flow=langgraph_chatbot_demo # langgraph_chatbot_demo or hpc_chatbot

python -m athos.examples.chatbot_example --flow $flow
