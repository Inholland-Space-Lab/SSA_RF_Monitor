#!../.venv/bin/python
import logging
import signal
import sys
from config import Config
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
    Server.stop()
    LCD.write("Stopped: " + _signo)
    sys.exit(0)


if __name__ == "__main__":
    # Register our shutdown handler to be called at signal "terminate"
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Start the server and add the camera(s)
    logger.info("starting")
    try:
        Config.start()
        LCD.start()
        Server.start()
    finally:
        sigterm_handler(signal.SIGTERM, 0)
