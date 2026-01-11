const toc = document.getElementById("toc")
let on_off = true

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