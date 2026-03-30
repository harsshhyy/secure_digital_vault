let keystrokes = [];
let holdTimes = [];
let flightTimes = [];
let lastKeyDown = null;
let lastKeyUp = null;
let lastTime = Date.now();
let trustScore = 100;

// 🖱️ Mouse
let mouseSpeeds = [];
let lastMouseTime = null;
let lastX = null;
let lastY = null;

// ⏱️ Session
let sessionStart = Date.now();

// ----- Helper to log events to backend -----
function logEvent(action, details={}) {
    fetch("/log_behavior", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ action, ...details })
    }).catch(err => console.error("Log error:", err));
}

// ----- Keyboard Tracking -----
document.addEventListener("keydown", (e) => {
    let now = Date.now();
    if (lastKeyUp !== null) flightTimes.push(now - lastKeyUp);
    lastKeyDown = now;
});

document.addEventListener("keyup", (e) => {
    let now = Date.now();
    if (lastKeyDown !== null) holdTimes.push(now - lastKeyDown);
    lastKeyUp = now;
    let diff = now - lastTime;
    keystrokes.push(diff);
    lastTime = now;
});

// ----- Mouse Tracking -----
document.addEventListener("mousemove", (e) => {
    let now = Date.now();
    if (lastMouseTime !== null && lastX !== null && lastY !== null) {
        let dist = Math.sqrt((e.clientX-lastX)**2 + (e.clientY-lastY)**2);
        let speed = dist / (now - lastMouseTime);
        mouseSpeeds.push(speed);
    }
    lastMouseTime = now;
    lastX = e.clientX;
    lastY = e.clientY;
});

// ----- Track Menu / Page Switch -----
document.querySelectorAll(".menu-link").forEach(link => {
    link.addEventListener("click", () => {
        logEvent("pageSwitch", { page: link.dataset.page });
    });
});

// ----- Track Clicks -----
document.querySelectorAll("button, a").forEach(el => {
    el.addEventListener("click", () => {
        logEvent("click", { element: el.innerText || el.href });
    });
});

// ----- Track Scroll -----
let lastScroll = window.scrollY;
document.addEventListener("scroll", () => {
    const scrollY = window.scrollY;
    const speed = Math.abs(scrollY - lastScroll);
    lastScroll = scrollY;
    logEvent("scroll", { scrollY, speed });
});

// ----- Save Note Functionality -----
function saveNote() {
    let note = document.getElementById("notesArea").value;
    fetch("/save_note", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ note })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        loadNotes();
        logEvent("saveNote", { length: note.length });
    });
}

// ----- Load Notes -----
function loadNotes() {
    fetch("/get_notes")
    .then(res => res.json())
    .then(data => {
        let list = document.getElementById("notesList");
        list.innerHTML = "";
        data.notes.forEach(n => {
            let li = document.createElement("li");
            li.innerText = n;
            list.appendChild(li);
        });
    });
}

window.onload = loadNotes;

// ----- Run every 5 seconds -----
setInterval(() => {
    if (keystrokes.length < 5) return;

    let avgTyping = keystrokes.reduce((a,b)=>a+b,0)/keystrokes.length;
    let avgHold = holdTimes.length ? holdTimes.reduce((a,b)=>a+b,0)/holdTimes.length : 0;
    let avgFlight = flightTimes.length ? flightTimes.reduce((a,b)=>a+b,0)/flightTimes.length : 0;
    let avgMouse = mouseSpeeds.length ? mouseSpeeds.reduce((a,b)=>a+b,0)/mouseSpeeds.length : 0;
    let sessionDuration = (Date.now() - sessionStart)/1000;
    let loginHour = new Date().getHours();

    // ===== Trust Score Logic =====
    if (avgTyping < 80 || avgTyping > 800) trustScore -= 10; else trustScore += 5;
    if (avgHold > 200 || avgHold < 30) trustScore -= 10;
    if (avgFlight > 300 || avgFlight < 30) trustScore -= 10;
    if (avgMouse > 2 || avgMouse < 0.01) trustScore -= 10;
    if (loginHour < 6 || loginHour > 23) trustScore -= 15;
    if (sessionDuration < 5) trustScore -= 5;

    if (trustScore > 100) trustScore = 100;
    if (trustScore < 0) trustScore = 0;

    // Update UI
    let trustElem = document.getElementById("trustScore");
    if (trustElem) trustElem.innerText = trustScore;
    let statusElem = document.getElementById("status");
    if (statusElem) {
        if (trustScore > 75) statusElem.innerText = "🟢 Normal";
        else if (trustScore > 50) statusElem.innerText = "🟡 Medium Risk";
        else statusElem.innerText = "🔴 High Risk";
    }

    // Log summary to backend
    logEvent("interactionSummary", {
        avgTyping,
        avgHold,
        avgFlight,
        avgMouse,
        sessionDuration
    });

    // Auto logout if too low
    if (trustScore <= 20) {
        alert("⚠️ Suspicious activity detected. Logging out...");
        window.location.replace("/logout");
    }

    // Reset buffers
    keystrokes = [];
    holdTimes = [];
    flightTimes = [];
    mouseSpeeds = [];

}, 5000);