// 1) Node built-ins
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// 2) Third-party libs
import { globSync } from "glob";
import { minify as minifyHtml } from "html-minifier-terser";
import { minify as minifyJs } from "terser";
import { transform as transformCss } from "lightningcss";

// 3) ESM-safe __dirname / __filename
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 4) Project paths
const ROOT = path.resolve(__dirname, "..");
const PUBLIC_DIR = path.join(ROOT, "public");
const DIST_DIR = path.join(ROOT, "dist");

// 5) Small helpers
async function pathExists(p) {
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

async function writeFileEnsuringDir(outPath, content) {
  await ensureDir(path.dirname(outPath));
  await fs.writeFile(outPath, content);
}

async function copyFileEnsuringDir(srcPath, outPath) {
  await ensureDir(path.dirname(outPath));
  await fs.copyFile(srcPath, outPath);
}

// 6) Main routine
async function main() {
  // Validate input dir exists
  if (!(await pathExists(PUBLIC_DIR))) {
    console.error(`❌ public/ directory not found at: ${PUBLIC_DIR}`);
    process.exit(1);
  }

  // Clean dist/ and recreate
  await fs.rm(DIST_DIR, { recursive: true, force: true });
  await ensureDir(DIST_DIR);

  // Find all files under public/ (relative paths)
  const relFiles = globSync("**/*", {
    cwd: PUBLIC_DIR,
    nodir: true,
    dot: true
  });

  for (const rel of relFiles) {
    const inPath = path.join(PUBLIC_DIR, rel);
    const outPath = path.join(DIST_DIR, rel);

    const ext = path.extname(rel).toLowerCase();
    
    // HTML
    if (ext === ".html") {
      const html = await fs.readFile(inPath, "utf8");
      const minified = await minifyHtml(html, {
        collapseWhitespace: true,
        removeComments: true,
        removeRedundantAttributes: true,
        removeEmptyAttributes: true,
        useShortDoctype: true,
        // Inline minification (safe defaults for many static sites)
        minifyCSS: true,
        minifyJS: true
      });
      await writeFileEnsuringDir(outPath, minified);
      continue;
    }

    // CSS
    if (ext === ".css") {
      const css = await fs.readFile(inPath); // Buffer
      const result = transformCss({
        filename: rel,
        code: css,
        minify: true
      });
      // result.code is Uint8Array (binary-safe)
      await writeFileEnsuringDir(outPath, result.code);
      continue;
    }

    // JS
    if (ext === ".js") {
      const js = await fs.readFile(inPath, "utf8");
      const result = await minifyJs(js, {
        compress: true,
        mangle: true
      });

      if (!result.code) {
        throw new Error(`Terser produced no output for: ${rel}`);
      }

      await writeFileEnsuringDir(outPath, result.code);
      continue;
    }

    // Everything else: copy as-is (images, fonts, etc.)
    await copyFileEnsuringDir(inPath, outPath);
  }

  console.log(`✅ Minified public/ → dist/ (${relFiles.length} files processed)`);
}

main().catch((err) => {
  console.error("❌ Build failed:", err);
  process.exit(1);
});
