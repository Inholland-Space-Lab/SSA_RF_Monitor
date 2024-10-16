import os
import time
from lib.grove import JHD1802
import logging


logger = logging.getLogger(__name__)


class LCD():

    lcd: JHD1802

    def start():
        logger.info("Starting LCD")

        try:
            LCD.lcd = JHD1802()

            LCD.lcd.backlight(False)
            time.sleep(1)

            LCD.lcd.backlight(True)
            LCD.lcd.setCursor(0, 0)
            LCD.write("Started At:")
        except Exception as e:
            logger.warning("Failed to Start LCD: " + str(e))

    def writeIP():
        ip = str(os.popen('hostname -I').read())
        logger.debug(ip)

        LCD.lcd.setCursor(0, 1)
        LCD.lcd.write(str(ip))

    @staticmethod
    def write(msg):
        if not hasattr(LCD, "lcd"):
            logger.warning("Failed to write to LCD: LCD not started.")
            return
        LCD.lcd.clear()
        LCD.lcd.setCursor(0, 0)
        LCD.lcd.write(str(msg))
        LCD.writeIP()
