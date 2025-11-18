async function initMap() {
    await google.maps.importLibrary("maps3d");
}

window.initMap = initMap;