(() => {
    const div = document.createElement("div");
    let para = document.createElement('p');
    para.innerHTML = `The server could not find <a href="${window.location.href}">${window.location.href}</a>.`;
    div.appendChild(para);

    para = document.createElement('p');
    para.innerHTML = `This link might be temporarily broken, or no longer exist permanently.
Please head back to our <a href="/">homepage</a>.`;
    div.appendChild(para);

    document.getElementById("notfound-msg").replaceWith(div)
})()