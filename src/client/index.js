// Function to move the dish to the target position
function updateDishPosition() {
    const azimuth = document.getElementById('azimuth').value;
    const elevation = document.getElementById('elevation').value;

    // Update goal position display
    document.getElementById('goal-azimuth').textContent = azimuth;
    document.getElementById('goal-elevation').textContent = elevation;

    // Send azimuth and elevation to the server
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
function updatePidValues(type) {
    const p = document.getElementById(`pid-p-${type}`).value || 0;
    const i = document.getElementById(`pid-i-${type}`).value || 0;
    const d = document.getElementById(`pid-d-${type}`).value || 0;

    // Send PID values to the server for either azimuth or elevation
    fetch(`${window.location.origin}/api/set-pid`, {
        method: "POST",
        body: JSON.stringify({ type: type, p: p, i: i, d: d }),
        headers: {
            "Content-type": "application/json",
        },
    });
}

// Function to periodically fetch the current dish position
function fetchCurrentPosition() {
    fetch(`${window.location.origin}/api/get-current-position`)
        .then(response => {
            console.log(response)
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            console.log(data)
            // Assuming `data` contains `{ azimuth: value, elevation: value }`
            document.getElementById('current-azimuth').textContent = data.azimuth;
            document.getElementById('current-elevation').textContent = data.elevation;
        })
        .catch(error => {
            console.error("Error fetching current position:", error);
        });
}

// Start polling the server for the current position every 0.5 seconds
setInterval(fetchCurrentPosition, 500);
