import MiniSearch from 'minisearch'
import { promises as fs } from "node:fs";

const LOCALES = ["en-SG", "en-US"]
const segmenter = new Intl.Segmenter(
    LOCALES,
    { "granularity": "word" }
)
const searcher = new MiniSearch({
    tokenize: (string, _fieldName) => Array.from(segmenter.segment(string))
        .map((obj) => obj.segment)
        .filter((txt) => txt.search(/[\p{L}\p{N}\p{S}]/v) >= 0), // check if string contains at least one letter, number or symbol
    processTerm: (term, _fieldName) => term.normalize("NFKC").trim().toLocaleLowerCase(LOCALES), // normalize unicode
    fields: ["title", "abstract", "authors", "text"],
    storeFields: ["html"],
    searchOptions: { fuzzy: true, prefix: true, boost: { "title": 2.0, "abstract": 1.5, "authors": 0.5 } }
})

const data = JSON.parse(await fs.readFile("search-index.json", "utf8"))
searcher.addAll(data)
const output = JSON.stringify(searcher.toJSON())
await fs.writeFile("public/search-index.json", output, "utf8")