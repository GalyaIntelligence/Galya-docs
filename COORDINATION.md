# Galya docs + disk archive coordination

Ordered checklist for bringing **https://galya.io/docs** live while freeing local disk.

## 1. Disk / S3 (local machine)

1. **Microlens** (~171G): `galya-infra/scripts/archive-local-data-to-s3.sh sync` → repeat until verify passes; log e.g. `~/galya-multi-encoder/microlens-s3-sync.log`. Destination: `s3://galya-fashion-data/local-archive/<hostname>/galya-multi-encoder/data/raw/microlens/`.
2. **Do not** `purge` microlens until verify OK (script enforces ≥95% remote size).
3. **LinkedIn raw** (`~/galya-sales-agent/data/raw/linkedin`): sync JSONL + `images/` to `s3://galya-ingest/brightdata/linkedin/`; delete local only after byte/count verify.
4. Queue other large trees per `galya-web/galya-infra/docs/local-data-s3-archive.md`.

## 2. Mintlify + DNS

1. Mintlify project **galya**: Host at **`/docs`**, domain **`galya.io`**.
2. Add Mintlify **TXT** verification in Cloudflare (no apex CNAME to Mintlify when proxying).
3. Deploy Worker: `cloudflare/mintlify-proxy` (CI or `wrangler deploy`).

## 3. GitHub secrets

| Repo | Secrets / vars |
|------|----------------|
| **Galya-docs** | `SPEAKEASY_API_KEY`, `MINTLIFY_API_KEY`, `MINTLIFY_PROJECT_ID_PROD`, `MINTLIFY_PROJECT_ID_DEV`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| **galya-api-new** | `SPEAKEASY_API_KEY`, `DOWNSTREAM_SDK_TOKEN` (Speakeasy registry publish + SDK gen) |

## 4. E2E

1. `galya-api-new` CI publishes OpenAPI → Speakeasy registry `galya-api-with-code-samples`.
2. Run **Mintlify Deploy** on Galya-docs (`docs_tag=latest`).
3. Confirm **Deploy docs Cloudflare proxy** succeeds.
4. Open **https://galya.io/docs** (and API reference tab).

## 5. Done when

- Microlens (and other archives) verified; purges reclaim disk as needed.
- Docs load at `https://galya.io/docs` with working navigation and OpenAPI reference.
