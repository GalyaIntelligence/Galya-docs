/**
 * Proxy galya.io/docs → galya.mintlify.site (Mintlify subpath hosting).
 * Route patterns in wrangler.toml; do NOT CNAME apex to Mintlify when the
 * marketing site lives on the same domain.
 */

const DEFAULTS = {
  MINTLIFY_SUBDOMAIN: "galya.mintlify.site",
  CUSTOM_DOMAIN: "galya.io",
  DOCS_BASE_PATH: "/docs",
};

function docsPathPattern(basePath) {
  const escaped = basePath.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`^${escaped}`);
}

export default {
  async fetch(request, env) {
    const docsUrl =
      env.MINTLIFY_SUBDOMAIN || DEFAULTS.MINTLIFY_SUBDOMAIN;
    const customUrl = env.CUSTOM_DOMAIN || DEFAULTS.CUSTOM_DOMAIN;
    const basePath = env.DOCS_BASE_PATH || DEFAULTS.DOCS_BASE_PATH;
    const docsRe = docsPathPattern(basePath);

    try {
      const urlObject = new URL(request.url);

      if (urlObject.pathname.startsWith("/.well-known/")) {
        return fetch(request);
      }

      if (
        docsRe.test(urlObject.pathname) ||
        /^\/mintlify-assets\//.test(urlObject.pathname) ||
        /^\/_mintlify\//.test(urlObject.pathname)
      ) {
        const url = new URL(request.url);
        url.hostname = docsUrl;

        const proxyRequest = new Request(url, request);
        proxyRequest.headers.set("Host", docsUrl);
        proxyRequest.headers.set("X-Forwarded-Host", customUrl);
        proxyRequest.headers.set("X-Forwarded-Proto", "https");
        const clientIp = request.headers.get("CF-Connecting-IP");
        if (clientIp) {
          proxyRequest.headers.set("CF-Connecting-IP", clientIp);
        }

        return fetch(proxyRequest);
      }
    } catch {
      // fall through
    }

    return fetch(request);
  },
};
