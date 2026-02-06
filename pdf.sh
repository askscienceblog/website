#!/bin/bash
for FILE in "page_vars/articles"/*; do
  if [ -f "$FILE" ]; then
    echo "Processing file: $FILE"
    jq ".markdown" $FILE -r | pandoc -f markdown -t context --citeproc --csl=apa.csl --template=pandoc.tex > main.tex
    mkdir -p static
    grep -oP "(?<=[\(\[\{\"']/static/)(.*?)(?=[\)\]\}\"'])" main.tex | while IFS= read -r line; do
        echo "$line" | jq -rR @uri | sed "s/^/https:\/\/cms.ayrj.org\/static\//" | xargs -P 30 -I {} curl -o "static/$line" {}
    done
    sed -i "s/\/static\//.\/static\//g" main.tex
    context main.tex
    pdfname=$(basename $FILE .json)
    npx wrangler r2 object put "static-assets/$pdfname.pdf" --file=main.pdf --remote
    echo "Uploaded $pdfname.pdf"
  fi
done