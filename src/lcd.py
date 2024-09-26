import os
import busio
import board
from lib.esp8266_i2c_lcd import I2cLcd
import logging

logger = logging.getLogger(__name__)


class LCD():

    lcd: I2cLcd

    def start():
        logger.debug("Starting")

        try:
            i2c = busio.I2C(board.SCL, board.SDA)

            LCD.lcd = I2cLcd(i2c, 0x3E, 2, 16)
            LCD.write("Started At:")
        except:
            logger.warning("Failed to Start LCD")

    def writeIP():
        ip = str(os.popen('hostname -I').read())
        logger.debug(ip)

        LCD.lcd.move_to(0, 1)
        LCD.lcd.putstr(str)

    def write(str):
        LCD.lcd.clear()
        LCD.lcd.move_to(0, 0)
        LCD.lcd.putstr(str)
        LCD.writeIP()
