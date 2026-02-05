#!/bin/bash

tasks=pytorch #,transfer
export ATHOS_LOG_LEVEL=DEBUG

python -m athos.examples.docs_rag_agent --flow lang_docs_react_agent --tasks $tasks
