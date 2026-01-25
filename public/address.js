(() => {
    const RANDOM = new pseudoRandom("ayrj.org")
    const xorStrings = (str1, str2) => {
        let result = '';
        const maxLength = Math.max(str1.length, str2.length);

        for (let i = 0; i < maxLength; i++) {
            const code1 = str1.charCodeAt(i) || 0;
            const code2 = str2.charCodeAt(i) || 0;

            const xoredCode = code1 ^ code2;

            result += String.fromCharCode(xoredCode);
        }

        return result;
    };

    for (const addr of Array.from(document.getElementsByTagName("address"))) {
        const enc = window.atob(addr.getAttribute("enc-addr"));
        addr.innerHTML = xorStrings(enc, RANDOM.randBytes(enc.length));
        addr.removeAttribute("enc-addr");
    }
})()