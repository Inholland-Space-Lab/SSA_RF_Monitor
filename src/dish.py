import logging
import time
from config import Config
from RPi import GPIO
from adafruit_bno055 import BNO055_I2C
import board
from rpi_hardware_pwm import HardwarePWM

from stepper import ControlledStepper, Direction, Stepper


logger = logging.getLogger(__name__)


class Dish:
    # The belt contains two motors with different pins
    # motors = list()
    azimuth_motor: Stepper
    elevation_motor: Stepper
    sensor: BNO055_I2C

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

        Dish.setup_sensors()
        time.sleep(1)

        def azimuth():
            return Dish.sensor.euler[0]

        def elevation():
            return Dish.sensor.euler[1]

        Dish.azimuth_motor = ControlledStepper(
            step_pin=27,
            dir_pin=4,
            enable_pin=22,
            resolution=400,
            pwm=HardwarePWM(pwm_channel=2, hz=1, chip=2),
            sensor=Dish.sensor,
            position_callback=azimuth)

        Dish.elevation_motor = ControlledStepper(
            step_pin=24,
            dir_pin=17,
            enable_pin=23,
            resolution=400,
            pwm=HardwarePWM(pwm_channel=3, hz=1, chip=2),
            sensor=Dish.sensor,
            position_callback=elevation
        )

        Dish.azimuth_motor.tune(-1, 0, -2.5)
        Dish.elevation_motor.tune(1, 0, 2.5)

    @staticmethod
    def setup_sensors():
        i2c = board.I2C()
        Dish.sensor = BNO055_I2C(i2c)

    @staticmethod
    def set_target(azimuth, elevation):
        logger.info(f"Setting target: {azimuth}, {elevation}")

        Dish.azimuth_motor.move_to_sync(degrees=azimuth)
        Dish.elevation_motor.move_to_sync(degrees=elevation)

    @staticmethod
    def tune_pid(p, i, d, elevation=False):
        if elevation:
            Dish.elevation_motor.tune(p, i, d)
        else:
            Dish.azimuth_motor.tune(p, i, d)

    @staticmethod
    def zero():
        Dish.azimuth_motor.zero()
        Dish.elevation_motor.zero()

    @staticmethod
    def positionListener(currentPos, targetPos, dir):
        logger.info(currentPos)

    @staticmethod
    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        Dish.azimuth_motor.stop()
        Dish.elevation_motor.stop()
