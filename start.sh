# Create all the required files and folders
mkdir logs
mkdir config
mv logs/latest.log logs/old.log
touch logs/latest.log

# Create a virtual environment (venv)
python -m venv --system-site-packages ./.venv

# Install python packages into the venv
./.venv/bin/pip install numpy --upgrade
# ./.venv/bin/pip install lgpio pigpio gpio   # gpio pins
./.venv/bin/pip install gpiozero            # gpio pins
./.venv/bin/pip install adafruit-circuitpython-bno055 #bno055 library

# Start the program
./.venv/bin/python ./src/main.py
