#!/bin/bash
echo "Processing file: $1"

if [ -f "$1" ]; then
  jq ".markdown" "$1" -r | pandoc -f markdown -t context --citeproc --csl=apa.csl --lua-filter=tbl.lua --template=pandoc.tex > main.tex
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
  sed -i "s/\/static\//.\/static\//g" main.tex
  context main.tex
  pdfname=$(basename "$1" .json)
  if [ -z "$PDF_DEV_MODE" ]; then
    npx wrangler r2 object put "static-assets/$pdfname.pdf" --file=main.pdf --remote
    echo "Uploaded $pdfname.pdf"
  else
    echo "PDF_DEV_MODE is set. Skipping upload of $1"
  fi
else
  echo "File: $1 not found"
fi