#!/usr/bin/env bash
# Keep the published spec's playground on the development API only.
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import re

path = Path("openapi/openapi.yaml")
if not path.exists():
    raise SystemExit("openapi/openapi.yaml is missing")

text = path.read_text()
pinned = (
    "servers:\n"
    "  - url: https://dev.api.galya.io\n"
    "    description: Development API\n"
)
text, n = re.subn(r"(?m)^servers:\n(?:^[ \t].*\n)*", pinned, text, count=1)
if n != 1:
    raise SystemExit("could not find the root servers block")

replacements = {
    "Cloudflare Workers API for indexing entities, linking taste history, and composing user state vectors.": "Index a catalog, link taste, and query it.",
    "Refreshes the parent's composed state vector in Turbopuffer when linking succeeds.": "Updates the parent's composed taste when the link succeeds.",
    "ADMIN_API_KEY not configured on the Worker": "Admin key is not configured",
    "ADMIN_API_KEY is not configured": "Admin key is not configured",
}
for old, new in replacements.items():
    text = text.replace(old, new)
text = re.sub(r"(?m)^  - url: https://\S*workers\.dev\n(?:    .*\n)*", "", text)
if "workers.dev" in text.split("paths:", 1)[0]:
    raise SystemExit("a non-public host is still in the spec header")

path.write_text(text)
print("playground server pinned to https://dev.api.galya.io")
PY
