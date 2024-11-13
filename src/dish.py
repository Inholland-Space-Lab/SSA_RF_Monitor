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
    azimuth_motor: Stepper
    elevation_motor: Stepper
    sensor: BNO055_I2C

    @staticmethod
    def start():
        logger.info("starting dish...")

        Dish._setup_sensors()
        time.sleep(1)
        Dish._setup_motors()
        # time.sleep(1)
        # Dish.calibrate()

    @staticmethod
    def _setup_motors():
        logger.debug("setup motors")

        def azimuth():
            return Dish.sensor.euler[0]

        def elevation():
            return Dish.sensor.euler[1]

        Dish.azimuth_motor = Stepper(
            dir_pin=4,
            enable_pin=22,
            pwm=HardwarePWM(pwm_channel=2, hz=1, chip=2),
            position_callback=azimuth
        )

        Dish.elevation_motor = Stepper(
            dir_pin=17,
            enable_pin=23,
            pwm=HardwarePWM(pwm_channel=3, hz=1, chip=2),
            position_callback=elevation
        )

        Dish.azimuth_motor.tune(-1, 0, -2.5)
        Dish.elevation_motor.tune(-1, 0, -2.5)

    @staticmethod
    def _setup_sensors():
        logger.debug("setup sensors")

        i2c = board.I2C()
        Dish.sensor = BNO055_I2C(i2c)

    @staticmethod
    def calibrate(calibration_time=20):
        logger.debug("Calibrating...")

        # Keep still at 6 different positions
        logger.debug("Calibrating Accelerometer")
        time.sleep(calibration_time)
        Dish.azimuth_motor.move_angle(degrees=45)
        time.sleep(calibration_time)
        Dish.elevation_motor.move_angle(degrees=45)
        time.sleep(calibration_time)
        Dish.azimuth_motor.move_angle(degrees=-90)
        time.sleep(calibration_time)
        Dish.elevation_motor.move_angle(degrees=-90)
        time.sleep(calibration_time)
        Dish.azimuth_motor.move_angle(degrees=45)
        time.sleep(calibration_time)
        Dish.elevation_motor.move_angle(degrees=45)
        logger.debug("Accelerometer Calibrated!")

        # Smooth movement
        logger.debug("Calibrating Magnetometer")
        Dish.elevation_motor.move_angle(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=20)
        Dish.elevation_motor.move_angle(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=20)
        Dish.elevation_motor.move_angle(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=-20)
        Dish.elevation_motor.move_angle(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=-20)

        Dish.elevation_motor.move_angle(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=-20)
        Dish.elevation_motor.move_angle(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=-20)
        Dish.elevation_motor.move_angle(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=20)
        Dish.elevation_motor.move_angle(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=20)

        # TODO: wait till completed
        logger.debug("Accelerometer Calibrated!")
        Dish.stop()

        logger.info(f"Calibration Complete: {Dish.sensor.calibration_status}")

    @staticmethod
    def toggle_pid():
        if Dish.azimuth_motor.do_pid or Dish.elevation_motor.do_pid:
            Dish.azimuth_motor.stop_pid()
            Dish.elevation_motor.stop_pid()
        else:
            Dish.azimuth_motor.start_pid()
            Dish.elevation_motor.start_pid()

    @staticmethod
    def set_target(azimuth, elevation):
        logger.info(f"Setting target: {azimuth}, {elevation}")

        Dish.azimuth_motor.set_target(degrees=azimuth)
        Dish.elevation_motor.set_target(degrees=elevation)

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
        try:
            Dish.azimuth_motor.stop()
            Dish.elevation_motor.stop()
        except Exception as e:
            logger.error(str(e))

    @staticmethod
    def log():
        pass
