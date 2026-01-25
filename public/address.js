(() => {
    for (const addr of Array.from(document.getElementsByTagName("address"))) {
        const enc = window.atob(window.atob(addr.getAttribute("enc-addr")));
        addr.innerHTML = enc;
        addr.removeAttribute("enc-addr");
    }
})()