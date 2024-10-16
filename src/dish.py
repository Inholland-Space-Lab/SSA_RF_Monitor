import logging
import time
from config import Config
from RPi import GPIO
from RpiMotorLib import RpiMotorLib


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
        Dish.motorlibDrive()

    def motorlibDrive():
        # define GPIO pins
        GPIO_pins = (14, 15, 18)  # Microstep Resolution MS1-MS3 -> GPIO Pin
        direction = 244       # Direction -> GPIO Pin
        step = 27      # Step -> GPIO Pin

        # Declare a instance of class pass GPIO pins numbers and the motor type
        motor = RpiMotorLib.A4988Nema(
            direction, step, GPIO_pins, "DRV8825")

        # call the function, pass the arguments
        motor.motor_go(False, "Full", 100, .01, False, .05)

    def manualDrive():
        GPIO.setmode(GPIO.BCM)
        step_pin = 27
        steps = 10000
        step_delay = 1
        GPIO.setup(step_pin, GPIO.OUT)
        for i in range(steps):
            time.sleep(step_delay/1000)
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(step_delay/1000)
            GPIO.output(step_pin, GPIO.LOW)

    def positionListener(currentPos, targetPos, dir):
        logger.info(currentPos)

    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        # for motor in Belt.motors:
        #     motor.Stop()
