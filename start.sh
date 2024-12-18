#!/bin/bash

# Create all the required files and folders
mkdir -p logs
mkdir -p config
mv logs/latest.log logs/old.log
touch logs/latest.log

# Create a virtual environment (venv)
python -m venv --system-site-packages ./.venv

# Install python packages into the venv
./.venv/bin/pip install numpy --upgrade
./.venv/bin/pip install rpi-lgpio               # gpio pins
./.venv/bin/pip install Mock.GPIO               # gpio pins on pc
./.venv/bin/pip install smbus                   # i2c
./.venv/bin/pip install adafruit-circuitpython-bno055 #bno055 library
./.venv/bin/pip install multiprocess            # non-blocking code
./.venv/bin/pip install simple-pid              # Stepper motor control
./.venv/bin/pip install adafruit-circuitpython-register
./.venv/bin/pip install adafruit-circuitpython-busdevice
./.venv/bin/pip install adafruit-circuitpython-bno055
./.venv/bin/pip install rpi-hardware-pwm

# List installed packages
./.venv/bin/pip list

# Script name or pattern to look for
PROGRAM_SCRIPT="main.py"

# Function to check if the program is running
is_running() {
    pgrep -f "$PROGRAM_SCRIPT" > /dev/null
}

# Function to stop the program if it's running
stop_program() {
    echo "Checking if $PROGRAM_SCRIPT is running..."
    if is_running; then
        echo "$PROGRAM_SCRIPT is running, stopping it..."
        pkill -f "$PROGRAM_SCRIPT"
        sleep 5  # Give time for the process to terminate
        echo "$PROGRAM_SCRIPT stopped."
    else
        echo "$PROGRAM_SCRIPT is not running."
    fi
}

# Stop any existing instance of the program
stop_program

# Start the program
echo "Starting $PROGRAM_SCRIPT..."
./.venv/bin/python ./src/main.py
