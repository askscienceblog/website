async function initMap() {
    await google.maps.importLibrary("maps3d");
}

window.initMap = initMap;
const map = document.querySelector("gmp-map-3d");
let globeSpin = false;

document.addEventListener("scroll", () => {
    const scr = Math.max(0.0, window.scrollY) / 200;

    if (scr <= 1.0) {
        globeSpin = false;
        zoomGlobe(map, scr);
    } else if (!globeSpin) {
        globeSpin = true;
        zoomGlobe(map, 1.0);

        let prev = null;
        requestAnimationFrame(function frame(time) {
            if (globeSpin) {
                spinGlobe(map, 360 * 0.05, prev ? ((time - prev) / 1000) : 0.0)
                prev = time;
                requestAnimationFrame(frame)
            }
        })
    }
});

function zoomGlobe(globe, t) {
    globe.flyCameraTo({
        endCamera: {
            center: { lat: lerp(1.352111, 0, ease(t)), lng: 103.819806, altitude: lerp(80000, 21000000, ease(t)) },
            roll: lerp(0, -23, ease(t))
        },
        durationMillis: 0
    })
}

function spinGlobe(globe, deg_vel, time) {
    globe.flyCameraTo({
        endCamera: {
            center: {
                lat: 0,
                lng: globe.center.lng - deg_vel * time,
                altitude: 20000000,
            },
            roll: -23,
        }
    })
}

function lerp(start, end, t) {
    return start * (1.0 - t) + end * t;
}

function ease(t) {
    return Math.pow(t, 3);
}