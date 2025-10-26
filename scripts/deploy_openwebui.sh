#!/bin/bash

docker compose --env-file .env -f integrations/openwebui/docker-compose.yml up --build
