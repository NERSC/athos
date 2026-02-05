#!/bin/bash

flow=lang_sfapi_agent # lang_sfapi_agent or smol_sfapi_agent
tasks=systems #,outages #,projects
export ATHOS_LOG_LEVEL=DEBUG

python -m athos.examples.sfapi_agent --flow $flow --tasks $tasks
