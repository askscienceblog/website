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
  pdfname=$(basename "$1" .json)
  if [ -z "${UPLOAD_PDF:-}" ]; then
    # never wait for keyboard input on a TeX error; the error still makes context exit non-zero
    context --nonstopmode main.tex
    echo "UPLOAD_PDF is not set. Skipping upload of $1"
    exit 0
  fi

  # Skip ConTeXt and the upload when the published PDF was built from exactly these inputs.
  # The fingerprint covers everything the PDF is made from: main.tex (the article's markdown as rendered by
  # pandoc with tbl.lua, apa.csl and pandoc.tex, after the edits above), the bytes of every image it loads
  # (downloaded afresh above, so a replaced image counts as a change), and the build files themselves.
  # It does not cover the ConTeXt version: after a ConTeXt or font update, set FORCE_PDF to rebuild every PDF.
  fingerprint=$(
    {
      echo "pdf fingerprint v1"
      sha256sum main.tex pdf.sh pandoc.tex tbl.lua apa.csl fonts.zip
      if [ -n "$images" ]; then
        while IFS= read -r line; do sha256sum "static/$line"; done <<< "$images"
      fi
    } | sha256sum | cut -d' ' -f1
  )
  # The record "<name>.pdf.build" sits next to the PDF in R2 and holds the fingerprint it was built from and the
  # PDF's own SHA-256. The PDF is skipped only if the record matches this fingerprint AND the PDF now in R2 has
  # the recorded hash, so a missing, partial or out-of-order upload, a PDF replaced by hand, or a lost record
  # always leads to a rebuild. Any failure to read either object also leads to a rebuild.
  rm -f published.pdf published.build
  if [ -n "${FORCE_PDF:-}" ]; then
    echo "FORCE_PDF is set: rebuilding $pdfname.pdf"
  elif ! npx wrangler r2 object get "static-assets/$pdfname.pdf.build" --file=published.build --remote > /dev/null 2>&1; then
    echo "No build record for $pdfname.pdf: building it"
  elif [ "$(sed -n -E 's/^inputs ([0-9a-f]{64})$/\1/p' published.build)" != "$fingerprint" ]; then
    echo "$pdfname.pdf inputs have changed: rebuilding it"
  elif ! npx wrangler r2 object get "static-assets/$pdfname.pdf" --file=published.pdf --remote > /dev/null 2>&1; then
    echo "$pdfname.pdf could not be read from R2: rebuilding it"
  elif [ "$(sed -n -E 's/^pdf ([0-9a-f]{64})$/\1/p' published.build)" != "$(sha256sum published.pdf | cut -d' ' -f1)" ]; then
    echo "$pdfname.pdf in R2 does not match its build record: rebuilding it"
  else
    rm -f published.pdf published.build
    echo "$pdfname.pdf is unchanged since its last upload: skipped"
    exit 0
  fi
  rm -f published.pdf published.build

  context --nonstopmode main.tex
  # the PDF goes up first and its record second, so a record is only written once its PDF is in R2
  # (if the record upload fails, the old record no longer matches the new PDF's hash, so the next build rebuilds)
  printf 'inputs %s\npdf %s\n' "$fingerprint" "$(sha256sum main.pdf | cut -d' ' -f1)" > main.build
  npx wrangler r2 object put "static-assets/$pdfname.pdf" --file=main.pdf --remote
  npx wrangler r2 object put "static-assets/$pdfname.pdf.build" --file=main.build --remote
  echo "Uploaded $pdfname.pdf"
else
  echo "File: $1 not found" >&2
  exit 1
fi