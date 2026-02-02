(() => {
    const div = document.createElement("div");
    let para = document.createElement('p');
    para.innerHTML = `The server could not find <span style="text-decoration:underline">${window.location.href}</span>.`;
    para.setAttribute("style", "text-wrap:balance")
    div.appendChild(para);

    para = document.createElement('p');
    para.innerHTML = `This link might be temporarily broken, or no longer exist permanently.
Please head back to our <a href="/">homepage</a>.`;
    para.setAttribute("style", "text-wrap:balance")
    div.appendChild(para);

    div.setAttribute("style","display:flex;flex-direction:column;align-items:center")
    document.getElementById("notfound-msg").replaceWith(div)
})()