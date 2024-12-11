import logging
import threading
import time
from config import Config
from RPi import GPIO
from adafruit_bno055 import BNO055_I2C
import board
from rpi_hardware_pwm import HardwarePWM

from stepper import Stepper


logger = logging.getLogger(__name__)

# This motor represents the entire hardware part of the satellite dish,
# meaning the azimuth and elevation stepper motors and the position sensor.
# This class contains methods to operate the Dish as a whole.
# This is what the web interface should interact with.
# As there is only one Dish to be controlled by this stepper, most methods are static.
# Meaning there can only be one instance (unlike the stepper class which has two)


class Dish:
    azimuth_motor: Stepper
    elevation_motor: Stepper
    sensor: BNO055_I2C
    pid_active = False

    # start the dish, is run at start of the program. Could be called to reboot the dish after it has crashed.
    # this should contain the startup sequence of the dish.
    @staticmethod
    def start():
        logger.info("starting dish...")

        Dish._setup_sensors()  # start the position sensor
        time.sleep(1)  # give the sensor one second to boot up
        Dish._setup_motors()  # start the stepper motors

        Dish.log()  # starts a log cycle to print debug data to the terminal every second

    @staticmethod
    def _setup_motors():
        logger.debug("setup motors")

        # These two methods serve as the position callback function used in Stepper.sensor_position.
        # These methods separate the different axes from the sensor and provide only one to each motor
        def azimuth():
            return Dish.sensor.euler[0]

        def elevation():
            return Dish.sensor.euler[1]

        # This creates one instance of the stepper class by calling Stepper.__init__
        # Here we assign the values to make each motor instance unique
        Dish.azimuth_motor = Stepper(
            dir_pin=4,
            enable_pin=22,
            pwm=HardwarePWM(pwm_channel=2, hz=1, chip=2),
            position_callback=azimuth
        )

        # This creates one instance of the stepper class by calling Stepper.__init__
        # Here we assign the values to make each motor instance unique
        Dish.elevation_motor = Stepper(
            dir_pin=17,
            enable_pin=23,
            pwm=HardwarePWM(pwm_channel=3, hz=1, chip=2),
            position_callback=elevation
        )

        # configure the default pid tunings for each motor.
        # Can be tweaked using the web interface during runtime.
        # When a stable set of values has been found that way, they can be copied here to make them the new default, and persistent across reboots.
        Dish.azimuth_motor.tune(-1, 0, -2.5)
        Dish.elevation_motor.tune(-1, 0, -2.5)

    # starts the Position sensor
    @staticmethod
    def _setup_sensors():
        logger.debug("setup sensors")

        i2c = board.I2C()  # configure the I2C bus
        # everything else is handled by the library
        Dish.sensor = BNO055_I2C(i2c)

    # this is the calibration sequence for the sensor.
    # The sensor documentation states there are certain requirements to calibrate the sensor properly
    # This involves maintaining 6 stable positions, and performing a figure-8 movement
    # It does this by calling a series of waypoints using Stepper.move_angle and Stepper.move_angle_sync
    # The difference between these methods is that one blocks the program, and the other does not.
    # This makes it possible to do compound movements by waiting for one motor to complete, but not the other
    # This way both orders are executed at the same time, but the program still waits for one to be complete.
    # Note that this only checks one motor to be complete, this should be the one that takes the longest time.
    # Therefore the motor with the longest path should use Stepper.move_angle and the shorter should use Stepper.move_angle_sync
    # This method blocks the rest of the program, including the web interface.
    # At the moment, this sequence only calibrates 6 out of 9 sensors.
    # used by webinterface in server.py at RequestHandler.do_GET
    @staticmethod
    def calibrate(calibration_time=2):
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
        time.sleep(calibration_time)
        logger.debug("Accelerometer Calibrated!")

        # Smooth movement
        logger.debug("Calibrating Magnetometer")
        Dish.elevation_motor.move_angle_sync(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=20)
        Dish.elevation_motor.move_angle_sync(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=20)
        Dish.elevation_motor.move_angle_sync(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=-20)
        Dish.elevation_motor.move_angle_sync(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=-20)

        Dish.elevation_motor.move_angle_sync(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=-20)
        Dish.elevation_motor.move_angle_sync(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=-20)
        Dish.elevation_motor.move_angle_sync(degrees=-20)
        Dish.azimuth_motor.move_angle(degrees=20)
        Dish.elevation_motor.move_angle_sync(degrees=20)
        Dish.azimuth_motor.move_angle(degrees=20)

        logger.debug("Accelerometer Calibrated!")
        # print calibration results to the console
        logger.info(f"Calibration Complete: {Dish.sensor.calibration_status}")

    # Toggles the pid controller on both stepper motors, keeping them synced
    # used by webinterface in server.py at RequestHandler.do_GET
    @staticmethod
    def toggle_pid():
        # Stop the motors if they were moving
        Dish.azimuth_motor.stop()
        Dish.elevation_motor.stop()

        logger.debug("Toggle PID: ")
        if Dish.pid_active:  # stop the pid
            logger.debug("stop")
            Dish.azimuth_motor.stop_pid()
            Dish.elevation_motor.stop_pid()
        else:
            logger.debug("start")  # start the pid
            Dish.azimuth_motor.start_pid()
            Dish.elevation_motor.start_pid()

        # Toggle the pid_active variable to be inverse of what it was before
        Dish.pid_active = not Dish.pid_active

    # Set a target for the pid controller to move towards
    # used by webinterface in server.py at RequestHandler.do_POST
    @staticmethod
    def set_target(azimuth, elevation):
        logger.info(f"Setting target: {azimuth}, {elevation}")

        Dish.azimuth_motor.set_target(degrees=azimuth)
        Dish.elevation_motor.set_target(degrees=elevation)

    # Set pid values of one of the motors
    # used by webinterface in server.py at RequestHandler.do_POST
    @staticmethod
    def tune_pid(p, i, d, elevation=False):
        if elevation:
            Dish.elevation_motor.tune(p, i, d)
        else:
            Dish.azimuth_motor.tune(p, i, d)

    # Move to zero point (not implemented)
    # used by webinterface in server.py at RequestHandler.do_GET
    @staticmethod
    def zero():
        Dish.azimuth_motor.zero()
        Dish.elevation_motor.zero()

    @staticmethod
    def positionListener(currentPos, targetPos, dir):
        logger.info(currentPos)

    # Stop both the motors, run when the progam exits or crashes
    @staticmethod
    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        try:
            Dish.azimuth_motor.disable()
            Dish.elevation_motor.disable()
        except Exception as e:
            logger.error(str(e))

    # Print "useful" data to the terminal and log file
    @staticmethod
    def log():
        logger.debug(
            f"\nAzimuth:\n{Dish.azimuth_motor}"
            f"Elevation:\n{Dish.elevation_motor}"
            f"Sensor pos: {Dish.sensor.euler}\n"
            f"Sensor calib: {Dish.sensor.calibration_status}"
        )

        # Call the same log again after one second
        timer = threading.Timer(
            1,
            Dish.log)
        timer.daemon = True  # Makes sure the timer stops when the process crashes
        timer.start()
