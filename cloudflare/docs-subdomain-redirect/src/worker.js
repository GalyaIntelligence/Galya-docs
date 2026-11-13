/**
 * docs.galya.io is retired. Docs live at https://galya.io/docs.
 *
 * - Every path 301s to the matching page under /docs (the old /beta prefix is
 *   dropped). Paths that no longer exist go to the docs introduction instead
 *   of a 404.
 * - Every response carries `X-Robots-Tag: noindex, nofollow`, so nothing on
 *   this host stays in search.
 * - robots.txt allows crawling by default so search engines and SEO tools can
 *   follow the redirects and move signals to galya.io/docs. Set
 *   ROBOTS_DISALLOW_ALL = "true" to serve `Disallow: /` instead.
 */

const NOINDEX = { "X-Robots-Tag": "noindex, nofollow" };

function targetPath(pathname, landing) {
  let p = pathname.replace(/\/+$/, "");
  p = p.replace(/^\/beta(?=\/|$)/, "");
  p = p.replace(/^\/docs(?=\/|$)/, "");
  if (p === "" || p === "/") return landing;
  return `/docs${p}`;
}

async function exists(origin, path) {
  try {
    const res = await fetch(`https://${origin}${path}`, {
      method: "HEAD",
      redirect: "manual",
      cf: { cacheTtl: 3600, cacheEverything: true },
    });
    return res.status >= 200 && res.status < 400;
  } catch {
    return false;
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const target = env.TARGET_ORIGIN || "https://galya.io";
    const mintlify = env.MINTLIFY_SUBDOMAIN || "galya.mintlify.site";
    const landing = env.LANDING_PATH || "/docs/introduction";

    if (url.pathname === "/robots.txt") {
      const body =
        env.ROBOTS_DISALLOW_ALL === "true"
          ? "User-agent: *\nDisallow: /\n"
          : "# docs.galya.io is retired; every URL redirects to https://galya.io/docs\nUser-agent: *\nAllow: /\n";
      return new Response(body, {
        headers: { "Content-Type": "text/plain; charset=utf-8", ...NOINDEX },
      });
    }

    let path = targetPath(url.pathname, landing);
    if (path !== landing && !(await exists(mintlify, path))) {
      path = landing;
    }

    return new Response(null, {
      status: 301,
      headers: {
        Location: `${target}${path}${url.search}`,
        "Cache-Control": "public, max-age=86400",
        ...NOINDEX,
      },
    });
  },
};
