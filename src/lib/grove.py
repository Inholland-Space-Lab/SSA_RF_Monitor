#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# Copyright (C) 2018  Seeed Technology Co.,Ltd.
#
# This is the library for Grove Base Hat
# which used to connect grove sensors for Raspberry Pi.
'''
This is the code for
    - `Grove - 16 x 2 LCD (Black on Red) <https://www.seeedstudio.com/Grove-16-x-2-LCD-Black-on-Re-p-3197.html>`_
    - `Grove - 16 x 2 LCD (Black on Yellow) <https://www.seeedstudio.com/Grove-16-x-2-LCD-Black-on-Yello-p-3198.html>`_
    - `Grove - 16 x 2 LCD (White on Blue) <https://www.seeedstudio.com/Grove-16-x-2-LCD-White-on-Blu-p-3196.html>`_

Examples:

    .. code-block:: python

        import time
        from grove.factory import Factory

        # LCD 16x2 Characters
        lcd = Factory.getDisplay("JHD1802")
        rows, cols = lcd.size()
        print("LCD model: {}".format(lcd.name))
        print("LCD type : {} x {}".format(cols, rows))

        lcd.setCursor(0, 0)
        lcd.write("hello world!")
        lcd.setCursor(0, cols - 1)
        lcd.write('X')
        lcd.setCursor(rows - 1, 0)
        for i in range(cols):
            lcd.write(chr(ord('A') + i))

        time.sleep(3)
        lcd.clear()
'''

# from grove.display.base import *
# from grove.i2c import Bus
import time
import sys
import smbus2 as smbus
from smbus2 import i2c_msg


class Bus:
    instance = None
    MRAA_I2C = 0

    # Use bus 1 by default, which is generally suitable for Raspberry Pi 2, 3, 4, etc.
    def __init__(self, bus=1):
        if not self.instance:
            self.instance = smbus.SMBus(bus)
        self.bus = bus
        self.msg = i2c_msg

    def __getattr__(self, name):
        return getattr(self.instance, name)


#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# Copyright (C) 2018  Seeed Technology Co.,Ltd.
#
# This is the library for Grove Base Hat
# which used to connect grove sensors for Raspberry Pi.
'''
Display Base Class
'''

# sphinx autoapi required
__all__ = [
    "Display",
    "TYPE_CHAR",
    "TYPE_GRAY",
    "TYPE_COLOR",
    "MAX_GRAY",
    "JHD1802"
]

TYPE_CHAR = 0
TYPE_GRAY = 1
TYPE_COLOR = 2

MAX_GRAY = 100


class Display(object):
    '''
    All display devices should inherit this virtual class,
    which provide infrastructure such as cursor and backlight inteface, etc.
    '''

    def __init__(self):
        self._cursor = False
        self._backlight = False

    # To be derived
    def _cursor_on(self, en):
        pass

    def cursor(self, enable=None):
        '''
        Enable or disable the backlight on display device,
        not all device support it.

        Args:
            enable (bool): Optional, ``True`` to enable, ``Flase`` to disable.
                           if not provided, only to get cursor status.

        Returns:
            bool: cursor status, ``True`` - on, ``False`` - off.
        '''
        if type(enable) == bool:
            self._cursor = enable
            self._cursor_on(enable)
        return self._cursor

    # To be derived
    def _backlight_on(self, en):
        pass

    def backlight(self, enable=None):
        '''
        Enable or disable the cursor on display device,
        not all device support it.

        Args:
            enable (bool): Optional, ``True`` to enable, ``Flase`` to disable.
                           if not provided, only to get cursor status.

        Returns:
            bool: backlight status, ``True`` - on, ``False`` - off.
        '''
        if type(enable) == bool:
            self._backlight = enable
            self._backlight_on(enable)
        return self._backlight


# sphinx autoapi required
# __all__ = ["JHD1802"]


class JHD1802(Display):
    '''
    Grove - 16 x 2 LCD, using chip JHD1802.
        - Grove - 16 x 2 LCD (Black on Yellow)
        - Grove - 16 x 2 LCD (Black on Red)
        - Grove - 16 x 2 LCD (White on Blue)

    Also, it's our class name,
    which could drive the above three LCDs.

    Args:
        address(int): I2C device address, default to 0x3E.
    '''

    def __init__(self, address=0x3E):
        self._bus = Bus()
        self._addr = address
        if self._bus.write_byte(self._addr, 0):
            print("Check if the LCD {} inserted, then try again"
                  .format(self.name))
            sys.exit(1)
        self.textCommand(0x02)
        time.sleep(0.1)
        self.textCommand(0x08 | 0x04)  # display on, no cursor
        self.textCommand(0x28)

    @property
    def name(self):
        '''
        Get device name

        Returns:
            string: JHD1802
        '''
        return "JHD1802"

    def type(self):
        '''
        Get device type

        Returns:
            int: ``TYPE_CHAR``
        '''
        return TYPE_CHAR

    def size(self):
        '''
        Get display size

        Returns:
            (Rows, Columns): the display size, in characters.
        '''
        # Charactor 16x2
        # return (Rows, Columns)
        return 2, 16

    def clear(self):
        '''
        Clears the screen and positions the cursor in the upper-left corner.
        '''
        self.textCommand(0x01)

    def draw(self, data, bytes):
        '''
        Not implement for char type display device.
        '''
        return False

    def home(self):
        '''
        Positions the cursor in the upper-left of the LCD.
        That is, use that location in outputting subsequent text to the display.
        '''
        self.textCommand(0x02)
        time.sleep(0.2)

    def setCursor(self, row, column):
        '''
        Position the LCD cursor; that is, set the location
        at which subsequent text written to the LCD will be displayed.

        Args:
            row   (int): the row at which to position cursor, with 0 being the first row
            column(int): the column at which to position cursor, with 0 being the first column

        Returns:
            None
        '''
        # print("setCursor: row={}, column={}".format(row,column))
        self.textCommand((0x40 * row) + (column % 0x10) + 0x80)

    def write(self, msg):
        '''
        Write character(s) to the LCD.

        Args:
            msg (string): the character(s) to write to the display

        Returns:
            None
        '''
        for c in msg:
            self._bus.write_byte_data(self._addr, 0x40, ord(c))

    def _cursor_on(self, enable):
        if enable:
            self.textCommand(0x0E)
        else:
            self.textCommand(0x0C)

    def textCommand(self, cmd):
        self._bus.write_byte_data(self._addr, 0x80, cmd)


def main():
    import time

    lcd = JHD1802()
    rows, cols = lcd.size()
    print("LCD model: {}".format(lcd.name))
    print("LCD type : {} x {}".format(cols, rows))

    lcd.backlight(False)
    time.sleep(1)

    lcd.backlight(True)
    lcd.setCursor(0, 0)
    lcd.write("hello world!")
    lcd.setCursor(0, cols - 1)
    lcd.write('X')
    lcd.setCursor(rows - 1, 0)
    for i in range(cols):
        lcd.write(chr(ord('A') + i))

    time.sleep(3)
    lcd.clear()


if __name__ == '__main__':
    main()
