#!/bin/bash

# This script provides an alternative to 'docker-compose' for running the Open WebUI and pipelines services using podman-hpc.
# It first creates a pod, then builds the pipelines image, and finally starts the two containers within the pod.
#
# USAGE:
# 1. Make sure you have a .env file in the project root with required environment variables:
#    - ATHOS_WORKSPACE (e.g., $(pwd) or ${SCRATCH}/athos/workspace)
#    - CBORG_API_URL, CBORG_API_KEY
#    - TAVILY_API_KEY
#    - GITHUB_TOKEN
#    - CLEARML_API_ACCESS_KEY, CLEARML_API_SECRET_KEY, CLEARML_API_HOST
# 2. Source the environment variables:
#    set -a; source .env; set +a
# 3. Run this script:
#    ./scripts/deploy_podmanhpc.sh
#

# Source env
set -a; source .env; set +a

set -e

# --- Configuration ---
POD_NAME="athos-services"
PIPELINES_IMAGE="athos-openwebui-pipelines:local"
PIPELINES_CONTAINER_NAME="athos-openwebui-pipelines"
WEBUI_IMAGE="ghcr.io/open-webui/open-webui:main"
WEBUI_CONTAINER_NAME="athos-openwebui-ui"
# WEBUI_PORT="9000"
# PIPELINES_PORT="9099"
WEBUI_PORT=19000
PIPELINES_PORT=19099
PIPELINES_API_KEY="M0i!XN3ybvd8"
ATHOS_PIPELINE_ENABLED_FLOWS=lang_web_agent,lang_sfapi_agent,lang_docs_agent,lang_filesystem_agent,lang_docs_react_agent,clearml_agent


# Setup directory for storing Open WebUI configuration
export OWUI_DATA_DIR=$SCRATCH/openwebui-data
mkdir -p "$OWUI_DATA_DIR"


# --- Pre-flight checks ---
REQUIRED_VARS="ATHOS_WORKSPACE CBORG_API_URL CBORG_API_KEY TAVILY_API_KEY GITHUB_TOKEN CLEARML_API_ACCESS_KEY CLEARML_API_SECRET_KEY CLEARML_API_HOST"
MISSING_VARS=""

for var in $REQUIRED_VARS; do
    if [ -z "${!var}" ]; then
        MISSING_VARS="$MISSING_VARS $var"
    fi
done

if [ -n "$MISSING_VARS" ]; then
    echo "Error: The following required environment variables are not set:"
    echo "$MISSING_VARS"
    exit 1
fi

# --- Cleanup previous runs ---
echo "--- Stopping and removing existing containers and pod ---"
set -x
podman-hpc stop ${PIPELINES_CONTAINER_NAME} >/dev/null 2>&1 || true
podman-hpc stop ${WEBUI_CONTAINER_NAME} >/dev/null 2>&1 || true
podman-hpc rm -f ${PIPELINES_CONTAINER_NAME} >/dev/null 2>&1 || true
podman-hpc rm -f ${WEBUI_CONTAINER_NAME} >/dev/null 2>&1 || true
podman-hpc pod rm -f ${POD_NAME} >/dev/null 2>&1 || true
set +x

# --- Create a Pod ---
echo "--- Creating pod '${POD_NAME}' ---"
podman-hpc pod create --name ${POD_NAME} -p ${WEBUI_PORT}:8080 -p ${PIPELINES_PORT}:9099

# --- Build pipelines image ---
echo "--- Building '${PIPELINES_IMAGE}' image ---"
echo "skipped"
#podman-hpc build -t ${PIPELINES_IMAGE} -f integrations/openwebui/Dockerfile.pipelines .
#podman-hpc migrate ${PIPELINES_IMAGE}

# --- Run pipelines container ---
echo "--- Starting '${PIPELINES_CONTAINER_NAME}' container ---"
podman-hpc run -d --pod ${POD_NAME} --name ${PIPELINES_CONTAINER_NAME} \
    --log-driver=k8s-file \
    --restart=unless-stopped \
    -v "$(pwd)/integrations/openwebui/pipelines:/app/pipelines:Z" \
    -v "$(pwd)/config:/workspace/config:ro,Z" \
    -v "${ATHOS_WORKSPACE}:/workspace/athos:Z" \
    -e PIPELINES_API_KEY=${PIPELINES_API_KEY} \
    -e PIPELINES_DIR=/app/pipelines \
    -e ATHOS_PIPELINE_CONFIG_PATH=/workspace/config/config.yaml \
    -e ATHOS_PIPELINE_ENABLED_FLOWS=${ATHOS_PIPELINE_ENABLED_FLOWS} \
    -e ATHOS_PIPELINE_DEFAULT_FLOW=lang_web_agent \
    -e ATHOS_WORKSPACE=/workspace/athos \
    -e CBORG_API_URL=${CBORG_API_URL} \
    -e CBORG_API_KEY=${CBORG_API_KEY} \
    -e TAVILY_API_KEY=${TAVILY_API_KEY} \
    -e GITHUB_TOKEN=${GITHUB_TOKEN} \
    -e CLEARML_API_ACCESS_KEY=${CLEARML_API_ACCESS_KEY} \
    -e CLEARML_API_SECRET_KEY=${CLEARML_API_SECRET_KEY} \
    -e CLEARML_API_HOST=${CLEARML_API_HOST} \
    ${PIPELINES_IMAGE}

# --- Run openwebui container ---
echo "--- Starting '${WEBUI_CONTAINER_NAME}' container ---"
podman-hpc run -d --pod ${POD_NAME} --name ${WEBUI_CONTAINER_NAME} \
    --log-driver=k8s-file \
    --restart=unless-stopped \
    -v "$OWUI_DATA_DIR":/app/backend/data \
    -e WEBUI_AUTH=True \
    ${WEBUI_IMAGE}

echo ""
echo "--- Services started! ---"
echo "Open WebUI should be available at http://localhost:${WEBUI_PORT}"
echo "Pipelines service is running inside the pod."
echo ""
echo "To view running logs:"
echo ""
echo "    podman-hpc logs --color -f $PIPELINES_CONTAINER_NAME $WEBUI_CONTAINER_NAME"
echo ""
