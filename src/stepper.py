import logging
import multiprocessing
import time
from config import Config
from RPi import GPIO

logger = logging.getLogger(__name__)


class Direction():
    clockwise = GPIO.HIGH
    counter_clockwise = GPIO.LOW

    def flip(direction):
        if direction == Direction.clockwise:
            return Direction.counter_clockwise
        elif direction == Direction.counter_clockwise:
            return Direction.clockwise


class Stepper():
    step_pin: int
    dir_pin: int
    enable_pin: int
    active: bool

    def __init__(self, step_pin, dir_pin, enable_pin):
        logger.info("Creating Stepper")
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.active = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup([step_pin, dir_pin, enable_pin], GPIO.OUT)

    def stop(self):
        self.active = False
        GPIO.output(self.enable_pin, GPIO.LOW)

    def do_steps_sync(self, *args):
        process = multiprocessing.Process(
            target=self.do_steps, args=args)
        process.daemon = True
        process.start()

    def do_steps(self, direction, step_count, delay_ms):
        if self.active:
            logger.warning("Stepper is already active!")
            return
        self.active = True
        logger.debug(f"doing {step_count} steps. Direction {direction}")
        GPIO.output(self.enable_pin, GPIO.HIGH)
        GPIO.output(self.dir_pin, direction)
        delay_s = delay_ms/1000

        for i in range(step_count):
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.LOW)

        self.active = False
