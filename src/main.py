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


# Configure logs to log both in the console and to a file
logger = logging.getLogger(__name__)
logging.basicConfig(handlers=[logging.FileHandler("logs/latest.log"),
                              logging.StreamHandler(sys.stdout)],
                    encoding='utf-8', level=logging.DEBUG)


def sigterm_handler(_signo, _stack_frame):
    # Gracefully stop the server when the program exits or crashes
    logger.info("stopping...")
    GPIO.cleanup()
    Server.stop()
    LCD.write("Stopped: " + str(_signo))
    sys.exit(0)


if __name__ == "__main__":
    # Register our shutdown handler to be called at signal "terminate"
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Start the server and add the camera(s)
    logger.info("starting")
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([23, 24], GPIO.OUT)
        GPIO.output(23, GPIO.HIGH)
        GPIO.output(24, GPIO.LOW)
        Config.start()
        LCD.start()
        Dish.start()
        Server.start()
    except Exception as e:
        logger.error(str(e))
    finally:
        sigterm_handler(signal.SIGTERM, 0)
