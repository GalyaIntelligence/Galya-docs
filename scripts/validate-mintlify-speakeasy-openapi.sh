#!/usr/bin/env bash
set -euo pipefail

DOCS_JSON="${1:-docs.json}"
REGISTRY_PATTERN='^https://registry\.speakeasy\.com/GalyaIntelligence/GalyaIntelligence/galya-api-with-code-samples@(latest|dev|[a-f0-9]{7,40})$'

url="$(jq -r '.navigation.tabs[] | select(.tab == "API reference") | .openapi' "$DOCS_JSON")"

if [ -z "$url" ] || [ "$url" = "null" ]; then
  echo "docs.json: missing API reference openapi URL" >&2
  exit 1
fi

if [[ "$url" == /* ]] || [[ "$url" == openapi/* ]]; then
  echo "docs.json must use Speakeasy registry URL, not local OpenAPI: ${url}" >&2
  exit 1
fi

if ! [[ "$url" =~ $REGISTRY_PATTERN ]]; then
  echo "docs.json openapi must match Speakeasy combined spec registry URL" >&2
  echo "Got: ${url}" >&2
  exit 1
fi

echo "Mintlify API reference is Speakeasy-generated: ${url}"
