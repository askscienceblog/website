const announce = document.getElementById("announcements");

function showAnnounce() {
    announce.removeAttribute("style")
}

function hideAnnounce() {
    announce.setAttribute("style", "display:none")
}
