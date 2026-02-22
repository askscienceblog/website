(async () => {
    const LOCALES = ["en-SG", "en-US"]
    const segmenter = new Intl.Segmenter(
        LOCALES,
        { "granularity": "word" }
    )
    const json = await (await fetch("/search-index.json")).text()
    const searcher = await MiniSearch.loadJSONAsync(json, {
        tokenize: (string, _fieldName) => Array.from(segmenter.segment(string))
            .map((obj) => obj.segment)
            .filter((txt) => txt.search(/[\p{L}\p{N}\p{S}]/v) >= 0), // check if string contains at least one letter, number or symbol
        processTerm: (term, _fieldName) => term.normalize("NFKC").trim().toLocaleLowerCase(LOCALES), // normalize unicode
        fields: ["title", "abstract", "authors", "text"],
        storeFields: ["html"],
        searchOptions: { fuzzy: true, prefix: true, boost: { "title": 2.0, "abstract": 1.5, "authors": 0.5 } }
    })

    const query = document.getElementById("search-q")
    const list = document.getElementsByClassName("article-list").item(0)

    query.addEventListener("input", (_) => {
        let input;
        if (query.value) {
            input = query.value;
        } else {
            input = MiniSearch.wildcard
        }
        list.innerHTML = ""
        searcher.search(input)
            .sort((a, b) => a.score - b.score)
            .forEach((obj) => {
                const li = document.createElement("li")
                li.innerHTML = obj.html
                list.appendChild(li)
            })
    })

    searcher.search(MiniSearch.wildcard)
        .sort((a, b) => a.score - b.score)
        .forEach((obj) => {
            const li = document.createElement("li")
            li.innerHTML = obj.html
            list.appendChild(li)
        })
})()