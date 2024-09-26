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

## Contributing

The following section will explain how to work with the raspberry pi, and update changes to the software.

### Updating code

The raspberry pi [automatically pulls](#startup-procedure) the latest version of the main branch of this github repo. Therefore, changes to the code can be uploaded to the raspberry pi by simply pushing commits to the main branch, and rebooting the raspberry pi.

The code should also be able to be run on any linux computer, or on windows via WSL. This allows you to debug the code on your own machine before committing, but this will of course not allow testing of GPIO pins.

For debugging on the raspberry pi, see [Connecting to the Raspberry](#connecting-to-the-raspberry)

### Startup procedure

The raspberry pi automatically pulls the latest version of the main branch of this github repo. It does this by running /home/isl/startDish.sh on startup/reboot using [crontab](https://wiki.archlinux.org/title/Cron#Crontab_format). This sh script will revert any local changes on the raspberry and override them with the git repo, it then runs the start.sh in the git repo. You can change this behavior by editing the startDish.sh file in the home folder on the raspberry.

### Connecting to the raspberry

Connecting to the raspberry can be done in several ways:

- [SSH](#ssh)
- [VNC](#vnc)
- [External Monitor](#external-monitor)

#### SSH

#### VNC

### External Monitor
