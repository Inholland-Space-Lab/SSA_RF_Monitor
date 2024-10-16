import os
import board
# from lib.esp8266_i2c_lcd import I2cLcd
import i2c_lcd
import logging

logger = logging.getLogger(__name__)


class LCD():

    lcd: i2c_lcd

    def start():
        logger.info("Starting LCD")

        try:

            i2c = board.I2C()

            # LCD.lcd = I2cLcd(i2c, 0x3E, 2, 16)
            LCD.lcd = i2c_lcd.lcd()
            LCD.write("Started At:")
        except Exception as e:
            logger.warning("Failed to Start LCD: " + str(e))

    def writeIP():
        ip = str(os.popen('hostname -I').read())
        logger.debug(ip)

        LCD.lcd.move_to(0, 1)
        LCD.lcd.putstr(str(ip))

    def write(msg):
        if not hasattr(LCD, "lcd"):
            logger.warning("Failed to write to LCD: LCD not started.")
            return
        LCD.lcd.clear()
        LCD.lcd.move_to(0, 0)
        LCD.lcd.putstr(str(msg))
        LCD.writeIP()
