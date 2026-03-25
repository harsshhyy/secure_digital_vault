let keystrokes = []
let mouseMoves = []
let mouseClicks = 0
let startTime = Date.now()

document.addEventListener("keydown", function(e){
    keystrokes.push(Date.now())
})

document.addEventListener("mousemove", function(e){
    mouseMoves.push({
        x: e.clientX,
        y: e.clientY,
        time: Date.now()
    })
})

document.addEventListener("click", function(){
    mouseClicks++
})

function calculateBehaviour(){

    if(keystrokes.length < 2) return

    let typingSpeed = keystrokes.length / ((Date.now()-startTime)/1000)

    let keyDelay = (keystrokes[keystrokes.length-1] - keystrokes[0]) / keystrokes.length / 1000

    let mouseSpeed = mouseMoves.length

    let clickRate = mouseClicks / ((Date.now()-startTime)/1000)

    let sessionTime = (Date.now()-startTime)/1000

    fetch("/behaviour", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            typing_speed: typingSpeed,
            key_delay: keyDelay,
            mouse_speed: mouseSpeed,
            mouse_click_rate: clickRate,
            session_time: sessionTime
        })
    })
    .then(res => res.json())
    .then(data => {
        if(data.action == "logout"){
            alert("Suspicious behaviour detected. Session locked.")
            window.location.href = "/login"
        }
    })
}

setInterval(calculateBehaviour, 5000)