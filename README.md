# SSA_RF_Monitor
This repo will contain all the code that will run on the raspberry pi that drives the SSA RF Monitor for Geostationary Satellites.

## Capabilities
With this software, the raspberry pi will have the following capabilities:

- Determine the current position and rotation of the entire monitor relative to the earth
- Determine the current position and rotation of the dish relative to the monitor and therefore earth
- Take the position of a GEO satellite from user input or database as input
- Use the previous three inputs in a closed loop to drive two stepper motors to point the dish to the satellite.
- Parse data from the dish via USB sdr dongle via gnuradio as output
- Host a web server to take input from a user and present output
- Display the current IP address on an LCD screen with which a user can reach the web server
- Host a hotspot with custom DNS for users to connect to so a custom url may be used instead of an IP address.
