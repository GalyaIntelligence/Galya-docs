# Galya-docs

Public [Mintlify](https://mintlify.com) site for the Galya API.

- **Guides** — MDX in this repo  
- **API reference** — Speakeasy combined OpenAPI (`galya-api-with-code-samples`) from the private [`galya-api-new`](https://github.com/GalyaIntelligence/galya-api-new) CI pipeline  

## Connect Mintlify

1. Create a Mintlify project linked to **`GalyaIntelligence/Galya-docs`** (public).
2. Production deployment branch: **`main`**. Optional dev project on branch **`dev`**.

## GitHub Actions secrets / variables (this repo)

| Name | Kind |
|------|------|
| `MINTLIFY_API_KEY` | Secret |
| `MINTLIFY_PROJECT_ID_PROD` | Variable |
| `MINTLIFY_PROJECT_ID_DEV` | Variable |

## Deploy flow

Private `galya-api-new` publishes to Speakeasy → SDK generates code samples → API repo runs combined spec → dispatches **`mintlify-deploy.yml`** here with `docs_tag=latest` or `dev`.

Manual:

```bash
gh workflow run mintlify-deploy.yml -R GalyaIntelligence/Galya-docs \
  -f docs_tag=latest -f git_ref=main
```

Enable **Public** on the combined spec in the Speakeasy Dashboard so Mintlify can fetch it.
