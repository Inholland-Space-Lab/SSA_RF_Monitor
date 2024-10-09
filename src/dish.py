import logging
import multiprocessing
from config import Config
import time
# from lib.stepper_motors_juanmf1 import (GenericStepper,
#                                         DRV8825MotorDriver,
#                                         )
from lib.stepper_motors_juanmf1.AccelerationStrategy import DynamicDelayPlanner, LinearAcceleration
from lib.stepper_motors_juanmf1.Controller import DRV8825MotorDriver
from lib.stepper_motors_juanmf1.Navigation import DynamicNavigation
from lib.stepper_motors_juanmf1.StepperMotor import GenericStepper

logger = logging.getLogger(__name__)

# The Belt class is not functional, it serves as inspiration as it also uses two stepper motors


class Dish:
    # The belt contains two motors with different pins
    # motors = list()

    # def configure():
    #     # create each of the motors and set their microstep config
    #     Belt.motors.append(DRV8825(dir_pin=13, step_pin=19,
    #                                enable_pin=12, mode_pins=(16, 17, 20)))
    #     for motor in Belt.motors:
    #         motor.SetMicroStep('hardward', '1/4step')

    @staticmethod
    def setupDriver(*, directionGpioPin, stepGpioPin) -> DRV8825MotorDriver:
        stepperMotor = GenericStepper(maxPps=2000, minPps=150)
        delayPlanner = DynamicDelayPlanner()
        navigation = DynamicNavigation()

        acceleration = LinearAcceleration(stepperMotor, delayPlanner)
        return DRV8825MotorDriver(stepperMotor, acceleration, directionGpioPin, stepGpioPin, navigation)

    def start():
        # start running the belt
        # TODO: start the belt continuously instead of 200 steps
        logger.debug("starting belt")
        motor1: DRV8825MotorDriver = Dish.setupDriver(
            directionGpioPin=17, stepGpioPin=27)  # 22

        motor1.stepClockWise(1000)
        # for motor in Belt.motors:
        #     speed = Config.getBeltSpeed()
        #     direction = Config.getBeltDirection()
        #     motor.TurnStep(Dir=direction, steps=0, stepdelay=1/speed)

    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        # for motor in Belt.motors:
        #     motor.Stop()
