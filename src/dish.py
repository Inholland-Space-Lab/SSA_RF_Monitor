import logging
import time
from config import Config
from RPi import GPIO

from stepper import Direction, Stepper


logger = logging.getLogger(__name__)


class Dish:
    # The belt contains two motors with different pins
    # motors = list()

    # def configure():
    #     # create each of the motors and set their microstep config
    #     Belt.motors.append(DRV8825(dir_pin=13, step_pin=19,
    #                                enable_pin=12, mode_pins=(16, 17, 20)))
    #     for motor in Belt.motors:
    #         motor.SetMicroStep('hardward', '1/4step')

    def start():
        # start running the belt
        # TODO: start the belt continuously instead of 200 steps
        logger.info("starting dish")
        # Dish.manualDrive()
        Dish.customLibDrive()

    def customLibDrive():
        motor = Stepper(step_pin=27, dir_pin=4, enable_pin=22)

        motor.do_steps_sync(Direction.clockwise, 10000, 1)
        motor.do_steps_sync(Direction.counter_clockwise, 10000, 1)

    def positionListener(currentPos, targetPos, dir):
        logger.info(currentPos)

    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        # for motor in Belt.motors:
        #     motor.Stop()
