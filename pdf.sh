#!/bin/bash
# stop at the first failing command, including inside pipelines, so a broken PDF is never uploaded
set -euo pipefail
echo "Processing file: $1"

if [ -f "$1" ]; then
  # -e fails if the JSON has no markdown, instead of rendering the text "null"
  jq ".markdown" "$1" -er | pandoc -f markdown -t context --citeproc --csl=apa.csl --lua-filter=tbl.lua --template=pandoc.tex > main.tex
  # site-relative links are dead in a downloaded PDF, so point them at the website
  sed -i -E "s#url\(/([^/])#url(https://ayrj.org/\1#g" main.tex
  mkdir -p static
  # Download every referenced image in parallel; exit non-zero if any fails so a PDF with missing images is never uploaded
  images=$(grep -oP "(?<=[\(\[\{\"']/static/)(.*?)(?=[\)\]\}\"'])" main.tex | sort -u || true)
  if [ -n "$images" ]; then
    while IFS= read -r line; do
      printf 'url = "https://cms.ayrj.org/static/%s"\noutput = "static/%s"\n' \
        "$(printf '%s' "$line" | jq -rR @uri)" "$(printf '%s' "$line" | sed 's/\\/\\\\/g')"
    done <<< "$images" | curl --config - \
      --parallel --parallel-immediate --parallel-max 50 \
      --fail --silent --show-error --location --create-dirs \
      --retry 3 --retry-all-errors --connect-timeout 10 --max-time 120 \
      || { echo "Failed to download images for $1" >&2; exit 1; }
    echo "Downloaded $(wc -l <<< "$images") images"
  fi
  # point the downloaded images at ./static, matching the same references the grep above found
  sed -i -E "s#([[({\"'])/static/#\1./static/#g" main.tex
  # never wait for keyboard input on a TeX error; the error still makes context exit non-zero
  context --nonstopmode main.tex
  pdfname=$(basename "$1" .json)
  if [ -z "${UPLOAD_PDF:-}" ]; then
    echo "UPLOAD_PDF is not set. Skipping upload of $1"
  else
    npx wrangler r2 object put "static-assets/$pdfname.pdf" --file=main.pdf --remote
    echo "Uploaded $pdfname.pdf"
  fi
else
  echo "File: $1 not found" >&2
  exit 1
fi