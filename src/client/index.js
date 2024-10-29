

function updateDishPosition() {
    const azimuth = document.getElementById('azimuth').value;
    const elevation = document.getElementById('elevation').value;

    // Placeholder: send azimuth and elevation data to server or backend
    console.log(`Setting Azimuth: ${azimuth}°, Elevation: ${elevation}°`);

    // Simulate updating the current position
    document.getElementById('current-azimuth').textContent = azimuth;
    document.getElementById('current-elevation').textContent = elevation;

    // Update additional data for example (like signal strength and status)
    document.getElementById('signal-strength').textContent = Math.floor(Math.random() * 100) + '%'; // Simulated signal strength
    document.getElementById('status').textContent = 'Moving...';

    setTimeout(() => {
        document.getElementById('status').textContent = 'Position Reached';
    }, 2000); // Simulate a delay for movement

    fetch(`${window.location.origin}/api/set-target`,
        {
            method: "POST",
            body: JSON
            .stringify
            ({
              azimuth: azimuth,
              elevation: elevation,
            }),
            headers: {
              "Content-type": "application/json",
            },
          })
}

function zeroDish() {

    fetch(`${window.location.origin}/api/zero`,
        {
            method: "POST",
            body: "",
            headers: {
              "Content-type": "application/json",
            },
          })
}

function updatePidValues() {
  const p = document.getElementById('pid-p').value;
  const i = document.getElementById('pid-i').value;
  const d = document.getElementById('pid-d').value;
  const time = document.getElementById('pid-time').value;

  fetch(`${window.location.origin}/api/set-pid`,
      {
          method: "POST",
          body: JSON
          .stringify
          ({
            p: p || 0,
            i: i || 0,
            d: d || 0,
            time: time || 0,
          }),
          headers: {
            "Content-type": "application/json",
          },
        })
}
