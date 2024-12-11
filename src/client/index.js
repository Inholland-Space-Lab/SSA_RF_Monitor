// Function to move the dish to the target position
function updateDishPosition() {
    // get the values entered in the input html elements
    // this will look in index.html for something that has id="azimuth" and takes the current value of that
    const azimuth = document.getElementById('azimuth').value;
    const elevation = document.getElementById('elevation').value;

    // Update goal position display
    document.getElementById('goal-azimuth').textContent = azimuth % 360;
    document.getElementById('goal-elevation').textContent = elevation % 360;

    // Send azimuth and elevation to the server in a post request
    // This ends up in server.py at RequestHandler.do_post
    fetch(`${window.location.origin}/api/set-target`, {
        method: "POST",
        body: JSON.stringify({ azimuth: azimuth, elevation: elevation }),
        headers: {
            "Content-type": "application/json",
        },
    });

    // Update status and signal strength for demonstration
    document.getElementById('status').textContent = 'Moving...';
    document.getElementById('signal-strength').textContent = Math.floor(Math.random() * 100) + '%';
}

// Function to zero the dish
// This ends up in server.py at RequestHandler.do_post
function zeroDish() {
    fetch(`${window.location.origin}/api/zero`, {
        method: "POST",
        body: "",
        headers: {
            "Content-type": "application/json",
        },
    });
}

// Function to update PID values
// This ends up in server.py at RequestHandler.do_post
function updatePidValues(type) {
    const p = document.getElementById(`pid-p-${type}`).value || 0;
    const i = document.getElementById(`pid-i-${type}`).value || 0;
    const d = document.getElementById(`pid-d-${type}`).value || 0;
    const time = document.getElementById(`pid-time`).value || 1;

    // Send PID values to the server for either azimuth or elevation
    fetch(`${window.location.origin}/api/set-pid`, {
        method: "POST",
        body: JSON.stringify({ type: type, p: p, i: i, d: d, time: time}),
        headers: {
            "Content-type": "application/json",
        },
    });
}

// Function to turn the pid controller on or off
// This ends up in server.py at RequestHandler.do_post
function togglePid() {
    fetch(`${window.location.origin}/api/toggle-pid`, {
        method: "POST",
        body: "",
        headers: {
            "Content-type": "application/json",
        },
    });
}

// Function to perform the calibration sequence
// This ends up in server.py at RequestHandler.do_post
function calibrate() {
    fetch(`${window.location.origin}/api/calibrate`, {
        method: "POST",
        body: "",
        headers: {
            "Content-type": "application/json",
        },
    });
}

// Function to periodically fetch the current dish position
// This ends up in server.py at RequestHandler.do_get
function fetchCurrentPosition() {
    fetch(`${window.location.origin}/api/get-current-position`) // perform the get request
        .then(response => {
            // after the response has been received
            console.log(response)
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json(); // read the response data and convert to json
        })
        .then(data => {
            // after data has been converted
            console.log(data)
            // Assuming `data` contains `{ azimuth: value, elevation: value }`
            document.getElementById('current-azimuth').textContent = data.azimuth;
            document.getElementById('current-elevation').textContent = data.elevation;
        })
        .catch(error => {
            // When 'data' did not contain azimuth or elevation, or something else went wrong
            console.error("Error fetching current position:", error);
        });
}

// Start polling the server for the current position every 0.5 seconds
setInterval(fetchCurrentPosition, 500);
