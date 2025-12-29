export default {
  async fetch(request, env) {
    const req_url = new URL(request.url);

    if (req_url.pathname.split("/")[1] == "static") {
      const file = await env.STATIC.get(req_url.pathname.split("/").slice(2).join("/"));
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