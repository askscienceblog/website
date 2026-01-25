let on_off = true
const toc = document.getElementById("TOC").querySelector("ul")

function toggleTOC(element) {
    if (on_off) {
        toc.setAttribute("style", "display:none")
        element.innerText = "Show Article Contents"
    } else {
        toc.removeAttribute("style")
        element.innerText = "Hide"
    }
    on_off = !on_off
}

(() => {
    const headings = []
    for (const anchor of document.getElementById("TOC").querySelectorAll("a")) {
        headings.push({ anchor, "heading": document.getElementById(anchor.getAttribute("href").slice(1)) })
    }

    const header_height = document.getElementById("header").getBoundingClientRect().bottom

    window.addEventListener("scroll", () => {
        for (const [ind, obj] of headings.entries()) {
            let h = obj.heading.getBoundingClientRect().y
            let next_height;
            try {
                next_height = headings[ind + 1].heading.getBoundingClientRect().y
            } catch {
                next_height = Infinity
            }
            if (h < window.innerHeight && header_height + 4 < next_height) {
                obj.anchor.setAttribute("class", "current")
            } else if (h >= window.innerHeight) {
                obj.anchor.setAttribute("class", "after")
            } else {
                obj.anchor.setAttribute("class", "before")
            }
        }
    })
})()