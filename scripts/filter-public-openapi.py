#!/usr/bin/env python3
"""Reduce the Speakeasy combined spec to customer-facing endpoints only.

The combined spec also documents admin, control-plane and internal routes
(workspace provisioning, health, agent runtime, OAuth callback, jobs, ...).
Those must not be published. This is an allowlist: an endpoint added to the
API stays out of the public docs until it is listed here.

Each kept operation also gets Mintlify page metadata (`x-mint.metadata`):
a meta description and `noindex: true`, so generated API reference pages
stay out of search while the hand-written guides are indexed.

Usage: scripts/filter-public-openapi.py [openapi/openapi.yaml]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# (method, path) pairs, grouped by product area.
PUBLIC_OPERATIONS: set[tuple[str, str]] = {
    # Index
    ("post", "/v1/index"),
    # Entity
    ("post", "/v1/entity"),
    ("get", "/v1/entity/{entityId}"),
    ("get", "/v1/entities/types"),
    ("get", "/v1/entity/{entityId}/contents"),
    ("post", "/v1/entity/{entityId}/contents"),
    ("delete", "/v1/entity/{entityId}/contents/{contentId}"),
    # Link
    ("post", "/v1/entity/{parentId}/link"),
    ("delete", "/v1/entity/{parentId}/link/{childId}"),
    ("get", "/v1/links"),
    # Query
    ("post", "/v1/search"),
    ("post", "/v1/recommend"),
    ("post", "/v1/rerank"),
    ("get", "/v1/models"),
    ("patch", "/v1/models/defaults"),
    # Cohorts and audience types (guides/audience-types.mdx)
    ("get", "/v1/swarms"),
    ("post", "/v1/swarms"),
    ("get", "/v1/swarms/{swarmId}"),
    ("patch", "/v1/swarms/{swarmId}"),
    ("delete", "/v1/swarms/{swarmId}"),
    ("get", "/v1/clusters"),
    ("get", "/v1/clusters/{clusterId}"),
    # Connectors (not the OAuth callback, which only the orchestrator calls)
    ("get", "/v1/connectors/registry"),
    ("get", "/v1/connectors/registry/{publicId}"),
    ("get", "/v1/connectors"),
    ("post", "/v1/connectors"),
    ("get", "/v1/connectors/{connectorId}"),
    ("patch", "/v1/connectors/{connectorId}"),
    ("delete", "/v1/connectors/{connectorId}"),
    ("post", "/v1/connectors/{connectorId}/test"),
    ("post", "/v1/connectors/{connectorId}/sync"),
    ("post", "/v1/connectors/requests"),
    # Agentic search
    ("get", "/v1/agentic-search/config"),
    ("put", "/v1/agentic-search/config"),
    ("get", "/v1/agentic-search/keys"),
    ("post", "/v1/agentic-search/keys"),
    ("delete", "/v1/agentic-search/keys/{keyId}"),
    ("get", "/v1/agentic-search/manifest"),
    ("post", "/v1/agentic-search/search"),
}

HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}
# Paths that must never appear in the public spec, even if allowlisted by mistake.
FORBIDDEN_PATH = re.compile(r"^/v1/(admin|internal)(/|$)|^/health$|^/$|/oauth/")


def plain(text: str) -> str:
    """Meta descriptions are plain text: drop markdown code and emphasis marks."""
    return re.sub(r"[`*_]", "", text).replace("\u2026", "...")


def scrub(text: str) -> str:
    """Remove infrastructure detail (vendors, internal routes) from prose."""
    text = re.sub(r"(?m)^.*(Admin routes|admin secret|Account provisioning routes).*\n?", "", text)
    # Prose mentions only; a backticked `turbopuffer` enum value is left alone.
    text = re.sub(r"(?<![`_])\bTurbopuffer\b ?", "", text)
    text = re.sub(r"\bPlanetScale (metadata|rows?)\b", r"stored \1", text)
    text = re.sub(r"\bPostgres\b", "the primary store", text)
    text = re.sub(r" ?\(`/v1/user-state`\)", "", text)
    return text


def scrub_tree(node):
    if isinstance(node, dict):
        return {k: scrub_tree(v) for k, v in node.items()}
    if isinstance(node, list):
        return [scrub_tree(v) for v in node]
    if isinstance(node, str):
        return scrub(node)
    return node


def describe(op: dict, method: str, path: str) -> str:
    summary = (op.get("summary") or "").strip().rstrip(".")
    first = (op.get("description") or "").strip().split("\n\n", 1)[0].replace("\n", " ")
    base = summary or f"{method.upper()} {path}"
    text = f"{base}. {first}" if first and first.rstrip(".") != summary else f"{base}."
    text = f"{text} {method.upper()} {path} in the Galya API reference."
    text = plain(text)
    if len(text) > 158:
        text = text[:155].rsplit(" ", 1)[0] + "..."
    return text


def collect_refs(node, out: set[str]) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/"):
            out.add(ref)
        for v in node.values():
            collect_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_refs(v, out)


def resolve(spec: dict, ref: str):
    node = spec
    for part in ref.lstrip("#/").split("/"):
        node = node.get(part.replace("~1", "/").replace("~0", "~"), {}) if isinstance(node, dict) else {}
    return node


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi/openapi.yaml")
    spec = scrub_tree(yaml.safe_load(path.read_text()))

    kept_paths: dict = {}
    dropped: list[str] = []
    for p, item in (spec.get("paths") or {}).items():
        new_item = {k: v for k, v in item.items() if k not in HTTP_METHODS}
        ops = 0
        for method, op in item.items():
            if method not in HTTP_METHODS:
                continue
            if (method, p) in PUBLIC_OPERATIONS and not FORBIDDEN_PATH.search(p):
                xm = op.setdefault("x-mint", {})
                meta = xm.setdefault("metadata", {})
                meta.setdefault("description", describe(op, method, p))
                meta["noindex"] = True
                new_item[method] = op
                ops += 1
            else:
                dropped.append(f"{method.upper()} {p}")
        if ops:
            kept_paths[p] = new_item
    spec["paths"] = kept_paths
    spec.pop("webhooks", None)

    # Keep only security schemes and tags that kept operations use.
    used_schemes: set[str] = set()
    used_tags: set[str] = set()
    for item in kept_paths.values():
        for method, op in item.items():
            if method in HTTP_METHODS:
                for req in op.get("security") or []:
                    used_schemes.update(req)
                used_tags.update(op.get("tags") or [])
    for req in spec.get("security") or []:
        used_schemes.update(req)
    if spec.get("tags"):
        spec["tags"] = [t for t in spec["tags"] if t.get("name") in used_tags]

    comps = spec.get("components") or {}
    if "securitySchemes" in comps:
        comps["securitySchemes"] = {
            k: v for k, v in comps["securitySchemes"].items() if k in used_schemes
        }

    # Prune components that no kept operation reaches.
    reachable: set[str] = set()
    frontier: set[str] = set()
    collect_refs(kept_paths, frontier)
    while frontier:
        ref = frontier.pop()
        if ref in reachable:
            continue
        reachable.add(ref)
        nxt: set[str] = set()
        collect_refs(resolve(spec, ref), nxt)
        frontier |= nxt - reachable
    for section, entries in list(comps.items()):
        if section == "securitySchemes" or not isinstance(entries, dict):
            continue
        comps[section] = {
            name: v for name, v in entries.items()
            if f"#/components/{section}/{name}" in reachable
        }
        if not comps[section]:
            del comps[section]

    missing = sorted(
        f"{m.upper()} {p}" for m, p in PUBLIC_OPERATIONS
        if m not in (kept_paths.get(p) or {})
    )

    text = yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=100)
    for word in ("Fargate", "Hermes", "/v1/admin", "/v1/internal", "AdminKey", "ADMIN_API_KEY",
                 "Admin-Key", "PlanetScale", "Turbopuffer", "/v1/user-state"):
        if word in text:
            raise SystemExit(f"public spec still mentions {word!r}; add a scrub or drop the endpoint")
    path.write_text(text)

    kept = sum(1 for i in kept_paths.values() for m in i if m in HTTP_METHODS)
    print(f"public spec: kept {kept} operations, dropped {len(dropped)}")
    for d in dropped:
        print(f"  dropped {d}")
    if missing:
        print("allowlisted but not in this spec (ok if not shipped yet): " + ", ".join(missing))


if __name__ == "__main__":
    main()
