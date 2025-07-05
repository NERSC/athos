#!/bin/bash

# ATHOS ServiceNow Agent Example Runner
# Runs the ServiceNow demonstration script

echo "🚀 Starting ATHOS ServiceNow Agent Example..."
echo "This demo shows ServiceNow operations using the ATHOS framework"
echo ""

if [ -z "$1" ]; then
  echo "Usage: $0 INCIDENT_NUMBER"
  exit 1
fi

python -m athos.examples.servicenow_agent \
  --config config/config.yaml \
  --tasks summary,triage,note,resolve \
  --incident "$1"

