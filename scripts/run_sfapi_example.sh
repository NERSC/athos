#!/bin/bash

flow=lc_sfapi_agent # lc_sfapi_agent or sfapi_agent
tasks=systems #,outages #,projects
export ATHOS_LOG_LEVEL=DEBUG

python -m athos.examples.sfapi_agent --flow $flow --tasks $tasks
