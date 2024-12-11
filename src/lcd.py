import os
import time
from lib.grove import JHD1802
import logging


logger = logging.getLogger(__name__)

# This class provides easy interaction between the program and the lcd api
# Main function of the lcd is to display the ip address where the web interface is accessible


class LCD():

    lcd: JHD1802

    # start the lcd screen, run on startup
    def start():
        logger.info("Starting LCD")

        try:
            LCD.lcd = JHD1802()  # Start the lcd api

            LCD.lcd.backlight(False)  # Turn off
            time.sleep(1)

            LCD.lcd.backlight(True)  # Turn on
            LCD.lcd.setCursor(0, 0)  # Reset
            LCD.write("Started At:")  # write the current ip, plus text
        except Exception as e:  # this runs when the lcd is not connected or crashes
            logger.warning("Failed to Start LCD (not connected?): " + str(e))

    def writeIP():
        ip = str(os.popen('hostname -I').read())  # Retrieve current ip address
        logger.debug(ip)  # print it to the console

        # Write the ip on the second line
        LCD.lcd.setCursor(1, 0)
        LCD.lcd.write(str(ip))

    @staticmethod
    def write(msg):
        # Check if the lcd has started correctly
        if not hasattr(LCD, "lcd"):
            logger.warning("Failed to write to LCD: LCD not started.")
            return
        # Clear the screen and write the text on the first line
        LCD.lcd.clear()
        LCD.lcd.setCursor(0, 0)
        LCD.lcd.write(str(msg))
        # write the ip on the second line
        LCD.writeIP()
