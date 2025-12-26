import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { globSync } from "glob";
import { minify as minifyHtml } from "html-minifier-terser";
import { transform as transformCss } from "lightningcss";
import { minify as minifyJs } from "terser";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT = path.resolve(__dirname, "..");
const PUBLIC_DIR = path.join(ROOT, "public");
const DIST_DIR = path.join(ROOT, "dist");

async function exists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function ensureDir(p) {
  await fs.mkdir(p, { recursive: true });
}

function relFromPublic(absPath) {
  return path.relative(PUBLIC_DIR, absPath);
}

function distPathFor(absPublicPath) {
  return path.join(DIST_DIR, relFromPublic(absPublicPath));
}

async function writeFileEnsuringDir(outPath, content) {
  await ensureDir(path.dirname(outPath));
  await fs.writeFile(outPath, content);
}

async function copyFileEnsuringDir(src, out) {
  await ensureDir(path.dirname(out));
  await fs.copyFile(src, out);
}

async function main() {
  if (!(await exists(PUBLIC_DIR))) {
    console.error(`No public/ directory found at: ${PUBLIC_DIR}`);
    process.exit(1);
  }

  // Clean dist/
  await fs.rm(DIST_DIR, { recursive: true, force: true });
  await ensureDir(DIST_DIR);

  const files = globSync("**/*", {
    cwd: PUBLIC_DIR,
    nodir: true,
    dot: true
  });

  for (const rel of files) {
    const inPath = path.join(PUBLIC_DIR, rel);
    const outPath = path.join(DIST_DIR, rel);
    const ext = path.extname(rel).toLowerCase();

    if (ext === ".html") {
      const html = await fs.readFile(inPath, "utf8");
      const minified = await minifyHtml(html, {
        collapseWhitespace: true,
        removeComments: true,
        removeRedundantAttributes: true,
        removeEmptyAttributes: true,
        useShortDoctype: true,

        minifyCSS: true,
        minifyJS: true
      });
      await writeFileEnsuringDir(outPath, minified);
      continue;
    }

    if (ext === ".css") {
      const css = await fs.readFile(inPath);
      const result = transformCss({
        filename: rel,
        code: css,
        minify: true
      });
      await writeFileEnsuringDir(outPath, result.code);
      continue;
    }

    if (ext === ".js") {
      const js = await fs.readFile(inPath, "utf8");
      const result = await minifyJs(js, {
        compress: true,
        mangle: true
      });

      if (!result.code) {
        throw new Error(`Terser failed to produce output for ${rel}`);
      }

      await writeFileEnsuringDir(outPath, result.code);
      continue;
    }

    // everything else (png, jpg, svg, woff2, etc.)
    await copyFileEnsuringDir(inPath, outPath);
  }

  console.log(`✅ Minified public/ → dist/ (${files.length} files processed)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});