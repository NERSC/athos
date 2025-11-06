#!/bin/bash

tasks=pytorch #,transfer

python -m athos.examples.docs_rag_agent --flow lc_docs_agent --tasks $tasks
