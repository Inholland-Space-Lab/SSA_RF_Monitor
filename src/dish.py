import logging
import time
from config import Config
from RPi import GPIO

from stepper import Direction, Stepper


logger = logging.getLogger(__name__)


class Dish:
    # The belt contains two motors with different pins
    # motors = list()
    azimuth_motor: Stepper
    elevation_motor: Stepper

    # def configure():
    #     # create each of the motors and set their microstep config
    #     Belt.motors.append(DRV8825(dir_pin=13, step_pin=19,
    #                                enable_pin=12, mode_pins=(16, 17, 20)))
    #     for motor in Belt.motors:
    #         motor.SetMicroStep('hardward', '1/4step')

    @staticmethod
    def start():
        # start running the belt
        # TODO: start the belt continuously instead of 200 steps
        logger.info("starting dish")

        Dish.azimuth_motor = Stepper(step_pin=27, dir_pin=4, enable_pin=22)
        Dish.elevation_motor = Stepper(step_pin=18, dir_pin=24, enable_pin=23)

    @staticmethod
    def set_target(azimuth, elevation):
        logger.info(f"Setting target: {azimuth}, {elevation}")

        Dish.azimuth_motor.move_to_sync(degrees=azimuth)
        Dish.elevation_motor.move_to_sync(degrees=elevation)

    @staticmethod
    def zero():
        Dish.azimuth_motor.position = 0
        Dish.elevation_motor.position = 0

    @staticmethod
    def positionListener(currentPos, targetPos, dir):
        logger.info(currentPos)

    @staticmethod
    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        # for motor in Belt.motors:
        #     motor.Stop()
