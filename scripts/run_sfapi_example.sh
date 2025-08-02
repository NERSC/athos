#!/bin/bash

tasks=systems,outages,projects

python -m athos.examples.sfapi_agent --tasks $tasks
