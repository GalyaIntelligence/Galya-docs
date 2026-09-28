# galya.io/docs (Mintlify + Cloudflare)

Public API docs live on Mintlify (`galya.mintlify.site`) and are exposed at **https://galya.io/docs** via a Cloudflare Worker reverse proxy. Do **not** CNAME the `galya.io` apex to Mintlify if the marketing site uses the same zone.

## Mintlify dashboard

1. Project **galya** → **Custom domain** → enable **Host at**, base path **`/docs`**, domain **`galya.io`**.
2. Complete domain verification (TXT records Mintlify shows). This is separate from the Worker routes.
3. Production Git branch: **`main`** (`GalyaIntelligence/Galya-docs`).

Mintlify stores the base path in project settings (not in `docs.json`). After changing `/docs`, redeploy from Mintlify or push to `main`.

## Cloudflare Worker

Source: `cloudflare/mintlify-proxy/`.

Routes (see `wrangler.toml`):

| Pattern | Purpose |
|---------|---------|
| `galya.io/docs*` | Docs pages (note `*` not `/*` for subpaths) |
| `galya.io/mintlify-assets/*` | Mintlify static assets |
| `galya.io/_mintlify/*` | API playground |
| Same for `www.galya.io` | Optional www |

Deploy manually:

```bash
cd cloudflare/mintlify-proxy
npx wrangler deploy
```

Or push to `main` / run **Deploy docs Cloudflare proxy** (needs `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`).

## DNS

- Keep existing apex/`www` records for the main site.
- Add Mintlify **TXT** verification records only (no apex CNAME to `.mintlify.app` when using the Worker).

## WAF (if docs 500 after ~30s)

Create a skip rule for `galya.io` where URI path starts with `/mintlify-assets/` (see [Mintlify Cloudflare firewall guide](https://www.mintlify.com/docs/deploy/cloudflare-firewall-troubleshooting)).

## Canonical URL

Set SEO canonical to `https://galya.io/docs` in Mintlify or via `docs.json` → `seo.metatags.canonical`.
