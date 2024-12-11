#!../.venv/bin/python
import logging
import signal
import sys
try:
    import RPi.GPIO as GPIO
    print("Detected Raspberry Pi environment.")
except:
    import Mock.GPIO as GPIO
    print("Not a Raspberry Pi. Switching to Mock.")
    sys.modules['RPi.GPIO'] = GPIO

from config import Config
from dish import Dish
from lcd import LCD
from server import Server

# This file is where the python program starts.

# Configure logs to log both in the console and to a file
logger = logging.getLogger(__name__)
logging.basicConfig(handlers=[logging.FileHandler("logs/latest.log"),
                              logging.StreamHandler(sys.stdout)],
                    encoding='utf-8', level=logging.DEBUG)

# this runs when the program exits or crashes


def sigterm_handler(_signo, _stack_frame):
    # Gracefully stop the server when the program exits or crashes
    logger.info("stopping...")
    Server.stop()
    Dish.stop()
    GPIO.cleanup()
    LCD.write("Stopped: " + str(_signo))
    sys.exit(0)


if __name__ == "__main__":  # This runs on startup:

    # Register our shutdown handler to be called at signal "terminate" (sigterm)
    # This signal is emitted when something in the program has crashed
    # Therefore we can run the shutdown handler after the program has crashed
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Start all the parts of the progarm
    logger.info("starting")
    try:
        Config.start()  # not important (yet)
        LCD.start()  # display ip address on lcd screen
        Dish.start()  # the motors and sensor
        Server.start()  # the web interface (this contains an infinite loop (waiting for user input) so it goes last)
    except Exception as e:  # This runs when something crashed
        logger.error(str(e))
    finally:  # This always runs when the rest is done, be it a crash or simply when the program finished
        sigterm_handler(signal.SIGTERM, 0)  # call the shutdown handler
