const CONTENT_TYPES = {
  otf: "font/otf",
  ttf: "font/ttf",
  woff: "font/woff",
  woff2: "font/woff2",
  css: "text/css",
  js: "text/javascript",
  svg: "image/svg+xml",
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  webp: "image/webp",
  pdf: "application/pdf",
};

export default {
  async fetch(request, env) {
    const req_url = new URL(request.url);

    if (req_url.pathname.split("/")[1] == "static") {
      // pathname is percent-encoded, but R2 keys are stored decoded (e.g. ’ rather than %E2%80%99);
      // fall back to the raw path for keys containing a literal "%" that is not an escape
      const raw = req_url.pathname.split("/").slice(2).join("/");
      let key = null;
      try {
        key = decodeURIComponent(raw);
      } catch {}
      let file = key ? await env.STATIC.get(key) : null;
      if (file == null && raw && key !== raw) {
        file = await env.STATIC.get(raw);
      }
      if (file != null) {
        const headers = new Headers()
        file.writeHttpMetadata(headers)
        // objects are uploaded without HTTP metadata; without a content type and validators,
        // browsers can't reuse <link rel="preload"> responses (e.g. fonts get fetched twice)
        if (!headers.has("Content-Type")) {
          const ext = file.key.split(".").pop().toLowerCase();
          if (ext in CONTENT_TYPES) headers.set("Content-Type", CONTENT_TYPES[ext]);
        }
        if (!headers.has("Cache-Control")) {
          headers.set("Cache-Control", "public, max-age=86400");
        }
        headers.set("ETag", file.httpEtag);
        headers.set("Last-Modified", file.uploaded.toUTCString());
        return new Response(file.body, { headers });
      }
    }

    const not_found_page = await (await env.ASSETS.fetch(new URL("/404.html", request.url))).text();
    return new Response(not_found_page, { status: 404, headers: { "Content-Type": "text/html" } });
  },
};