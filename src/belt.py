import logging
import multiprocessing
from config import Config
import time
from lib.DRV8825 import DRV8825

logger = logging.getLogger(__name__)

# The Belt class is not functional, it serves as inspiration as it also uses two stepper motors


class Belt:
    # The belt contains two motors with different pins
    motors = list()

    def configure():
        # create each of the motors and set their microstep config
        Belt.motors.append(DRV8825(dir_pin=13, step_pin=19,
                                   enable_pin=12, mode_pins=(16, 17, 20)))
        for motor in Belt.motors:
            motor.SetMicroStep('hardward', '1/4step')

    def start():
        # start running the belt
        # TODO: start the belt continuously instead of 200 steps
        logger.debug("starting belt")

        for motor in Belt.motors:
            speed = Config.getBeltSpeed()
            direction = Config.getBeltDirection()
            motor.TurnStep(Dir=direction, steps=0, stepdelay=1/speed)

    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        for motor in Belt.motors:
            motor.Stop()


Belt.configure()
