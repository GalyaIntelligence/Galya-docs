#!/usr/bin/env bash
set -euo pipefail

DOCS_TAG="${1:-latest}"
DOCS_JSON="${2:-docs.json}"
REGISTRY_BASE="https://registry.speakeasy.com/GalyaIntelligence/GalyaIntelligence/galya-api-with-code-samples"
OPENAPI_URL="${REGISTRY_BASE}@${DOCS_TAG}"

tmp="$(mktemp)"
jq --arg url "$OPENAPI_URL" \
  '.navigation.tabs |= map(if .tab == "API reference" then .openapi = $url else . end)' \
  "$DOCS_JSON" > "$tmp"
mv "$tmp" "$DOCS_JSON"

echo "Set API reference OpenAPI URL to Speakeasy combined spec: ${OPENAPI_URL}"
