export default {
  async fetch(request, env) {
    const req_url = new URL(request.url);

    if (req_url.pathname.split("/")[1] == "static") {
      // pathname is percent-encoded, but R2 keys are stored decoded (e.g. ’ rather than %E2%80%99)
      let key = null;
      try {
        key = decodeURIComponent(req_url.pathname.split("/").slice(2).join("/"));
      } catch {}
      const file = key == null ? null : await env.STATIC.get(key);
      if (file != null) {
        const headers = new Headers()
        file.writeHttpMetadata(headers)
        return new Response(file.body, { headers });
      }
    }

    const not_found_page = await (await env.ASSETS.fetch(new URL("/404.html", request.url))).text();
    return new Response(not_found_page, { status: 404, headers: { "Content-Type": "text/html" } });
  },
};