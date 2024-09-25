# Create all the required files and folders
mkdir logs
mkdir pictures
mkdir config
mv logs/latest.log logs/old.log
touch logs/latest.log

# Create a virtual environment (venv)
python -m venv --system-site-packages ./.venv

# Install python packages into the venv
./.venv/bin/pip install numpy --upgrade
./.venv/bin/pip install lgpio pigpio gpio   # gpio pins
./.venv/bin/pip install gpiozero            # Button input
./.venv/bin/pip install hx711               # Load cell
./.venv/bin/pip install picamera2           # Camera
./.venv/bin/pip install smbus rpi-lcd upymenu             # LCD Menu
./.venv/bin/pip install adafruit-circuitpython-charlcd

# Start the program
./.venv/bin/python ./src/main.py
