(async () => {
    const LOCALES = ["en-SG", "en-US"]
    const SPACES_ONLY = /^[\p{M}\p{Z}\p{C}]*$/v
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
    const previousSelected = new Set();

    const f = (_) => {
        let input;
        if (query.value) {
            input = query.value;
        } else {
            input = MiniSearch.wildcard
        }
        list.innerHTML = ""

        console.log(previousSelected)
        searcher.search(input)
            .sort((a, b) => a.score - b.score)
            .forEach((obj) => {
                const li = document.createElement("li")
                li.innerHTML = obj.html
                const walker = document.createTreeWalker(li, NodeFilter.SHOW_TEXT)
                let node = walker.nextNode()
                const mactchedTerms = new Set(obj.terms)

                let nodes = []
                while (node) {
                    const k = Array.from(segmenter.segment(node.nodeValue)) //recreate segmentation process
                        .filter((segment) =>
                            mactchedTerms.has(segment.segment.normalize("NFKC").trim().toLocaleLowerCase(LOCALES)))
                        .map((c) => [c.index, c.index + c.segment.length])
                    if (k.length > 0) {
                        nodes.push({ node, "values": k })
                    }
                    node = walker.nextNode()
                }

                for (const thisNode of nodes) {
                    thisNode.node.parentNode.insertBefore(
                        document.createTextNode(
                            thisNode.node.nodeValue.slice(0, thisNode.values[0][0])
                        ),
                        thisNode.node
                    );
                    const text = thisNode.node.nodeValue;
                    let prevNode = document.createElement("mark");
                    prevNode.innerText = text.slice(thisNode.values[0][0], thisNode.values[0][1])
                    thisNode.node.parentNode.insertBefore(prevNode, thisNode.node)


                    for (let i = 1; i < thisNode.values.length; i++) {
                        const currText = text.slice(thisNode.values[i - 1][1], thisNode.values[i][0])
                        if (SPACES_ONLY.test(currText)) {
                            prevNode.innerText += currText + text.slice(thisNode.values[i][0], thisNode.values[i][1])
                        } else {
                            thisNode.node.parentNode.insertBefore(
                                document.createTextNode(currText), thisNode.node
                            )
                            prevNode = document.createElement("mark")
                            prevNode.innerText = text.slice(thisNode.values[i][0], thisNode.values[i][1])
                            thisNode.node.parentNode.insertBefore(prevNode, thisNode.node)
                        }
                    }

                    thisNode.node.parentNode.insertBefore(
                        document.createTextNode(
                            text.slice(thisNode.values[thisNode.values.length - 1][1])
                        ),
                        thisNode.node
                    )
                    thisNode.node.parentNode.removeChild(thisNode.node)
                }

                li.firstElementChild.setAttribute("doc-id", obj.id)
                li.firstElementChild.addEventListener(
                    "toggle",
                    (e) => {
                        if (e.newState === "open") {
                            previousSelected.add(li.firstElementChild.getAttribute("doc-id"))
                        } else {
                            previousSelected.delete(li.firstElementChild.getAttribute("doc-id"))
                        }
                    }
                )
                if (previousSelected.has(obj.id.toString())) {
                    li.firstElementChild.setAttribute("open", "")
                }
                list.appendChild(li)
            })
    }
    query.addEventListener("input", f)
    f()
})()