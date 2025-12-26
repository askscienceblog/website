function change_nav(select) {

    switch (select.value.toLowerCase()) {

        case "articles":
            window.location.href = "/articles";
            break;
        case "story & team":
            window.location.href = "/about-us";
            break;
        case "contact us":
            window.location.href = "/about-us#footer ";
            break;
        case "for authors":
            window.location.href = "/publish";
            break;
        case "for referees":
            window.location.href = "/publish";
            break;
    }


    select.options.selectedIndex = 0;
}