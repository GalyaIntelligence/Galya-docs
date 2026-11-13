#!/usr/bin/env bash
# Point the published spec's playground at the production API.
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
    "  - url: https://api.galya.io\n"
    "    description: Production\n"
)
text, n = re.subn(r"(?m)^servers:\n(?:^[ \t].*\n)*", pinned, text, count=1)
if n != 1:
    raise SystemExit("could not find the root servers block")

replacements = {
    "ADMIN_API_KEY not configured on the Worker": "Admin key is not configured",
    "ADMIN_API_KEY is not configured": "Admin key is not configured",
}
for old, new in replacements.items():
    text = text.replace(old, new)
text = re.sub(r"(?m)^  - url: https://\S*workers\.dev\n(?:    .*\n)*", "", text)
header = text.split("paths:", 1)[0]
if "workers.dev" in header or "dev.api.galya.io" in header:
    raise SystemExit("a non-production host is still in the spec header")

path.write_text(text)
print("playground server pinned to https://api.galya.io")
PY
