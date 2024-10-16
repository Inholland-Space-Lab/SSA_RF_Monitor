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

        # Dish.manualDrive()
        Dish.motorHome()

    @staticmethod
    def motorHome():

        Dish.azimuth_motor.do_steps_sync(Direction.clockwise, 1000, 1)
        Dish.azimuth_motor.do_steps_sync(Direction.counter_clockwise, 1000, 1)

    @staticmethod
    def set_target(azimuth, elevation):
        logger.info(f"Setting target: {azimuth}, {elevation}")

        steps_per_rev = 360 / 1.8 * (19+(38/187))
        target_azimuth = azimuth / 360 * steps_per_rev
        current_azimuth = Dish.azimuth_motor.position
        azimuth_steps = current_azimuth - target_azimuth

        logger.debug(f"Current Position {current_azimuth}\n"
                     f"Target Position {target_azimuth}\n"
                     f"Taking {azimuth_steps} steps")

        if azimuth_steps > 0:
            Dish.azimuth_motor.do_steps_sync(
                Direction.counter_clockwise, int(azimuth_steps), 1)
        else:
            Dish.azimuth_motor.do_steps_sync(
                Direction.clockwise, - int(azimuth_steps), 1)

    @staticmethod
    def positionListener(currentPos, targetPos, dir):
        logger.info(currentPos)

    @staticmethod
    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        # for motor in Belt.motors:
        #     motor.Stop()
