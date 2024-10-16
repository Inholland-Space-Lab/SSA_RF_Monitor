import logging
import time
from config import Config
from RPi import GPIO
from stepper_motors_juanmf1.AccelerationStrategy import DynamicDelayPlanner, ExponentialAcceleration, LinearAcceleration
from stepper_motors_juanmf1.Controller import DRV8825MotorDriver
from stepper_motors_juanmf1.Navigation import DynamicNavigation
from stepper_motors_juanmf1.StepperMotor import GenericStepper

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

    @staticmethod
    def setupDriver(*, directionGpioPin, stepGpioPin, enableGpioPin) -> DRV8825MotorDriver:
        stepperMotor = GenericStepper(
            maxPps=2000, minPps=150, maxSleepTime=1/2000, minSleepTime=1/150)
        delayPlanner = DynamicDelayPlanner()
        navigation = DynamicNavigation()

        acceleration = ExponentialAcceleration(stepperMotor, delayPlanner, 1)
        return DRV8825MotorDriver(stepperMotor=stepperMotor, accelerationStrategy=acceleration, directionGpioPin=directionGpioPin, stepGpioPin=stepGpioPin, enableGpioPin=enableGpioPin, navigation=navigation)

    def start():
        # start running the belt
        # TODO: start the belt continuously instead of 200 steps
        logger.info("starting dish")

        GPIO.setmode(GPIO.BCM)
        step_pin = 27
        steps = 1000
        step_delay = 4
        GPIO.setup(step_pin, GPIO.OUT)
        for i in range(steps):
            time.sleep(step_delay/1000)
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(step_delay/1000)
            GPIO.output(step_pin, GPIO.LOW)
        # motor1: DRV8825MotorDriver = Dish.setupDriver(
        #     directionGpioPin=4, stepGpioPin=27, enableGpioPin=22)  # 22

        # logger.info(motor1.getCurrentPosition())
        # motor1.stepClockWise(200)
        # logger.info(motor1.getCurrentPosition())
        # for motor in Belt.motors:
        #     speed = Config.getBeltSpeed()
        #     direction = Config.getBeltDirection()
        #     motor.TurnStep(Dir=direction, steps=0, stepdelay=1/speed)

    def positionListener(currentPos, targetPos, dir):
        logger.info(currentPos)

    def stop():
        # stop each of the motors
        logger.info('stopping motors')
        # for motor in Belt.motors:
        #     motor.Stop()
