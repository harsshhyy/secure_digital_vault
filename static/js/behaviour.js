let keystrokes = []
let mouseMoves = []

document.addEventListener("keydown", function () {

    let time = new Date().getTime()
    keystrokes.push(time)

})

document.addEventListener("mousemove", function (e) {

    mouseMoves.push({
        x: e.clientX,
        y: e.clientY,
        time: new Date().getTime()
    })

})

setInterval(function () {

    let typingSpeed = 0
    let mouseSpeed = 0

    // Calculate typing speed
    if (keystrokes.length > 1) {

        let duration = keystrokes[keystrokes.length - 1] - keystrokes[0]

        typingSpeed = keystrokes.length / (duration / 1000)

    }

    // Calculate mouse speed
    if (mouseMoves.length > 1) {

        let dist = 0

        for (let i = 1; i < mouseMoves.length; i++) {

            let dx = mouseMoves[i].x - mouseMoves[i - 1].x
            let dy = mouseMoves[i].y - mouseMoves[i - 1].y

            dist += Math.sqrt(dx * dx + dy * dy)
        }

        let duration = mouseMoves[mouseMoves.length - 1].time - mouseMoves[0].time

        mouseSpeed = dist / (duration / 1000)

    }

    fetch("/behaviour", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            typing_speed: typingSpeed,
            mouse_speed: mouseSpeed
        })
    })
        .then(res => res.json())
        .then(data => {

            if (data.status === "suspicious") {

                alert("Suspicious behaviour detected! Vault locked.")
                window.location = "/login"

            }

        })

    keystrokes = []
    mouseMoves = []

}, 5000)