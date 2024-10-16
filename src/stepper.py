import math
import threading
import queue
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
    position: int
    gear_ratio: float
    resolution: int

    @property
    def steps_per_rev(self):
        return self.resolution * self.gear_ratio

    def __init__(self, step_pin, dir_pin, enable_pin, resolution=3200, gear_ratio=(19+(38/187))):
        # Define Pins
        logger.info("Creating Stepper")
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.gear_ratio = gear_ratio
        self.resolution = resolution
        self.position = 0

        # Setup the thread and queue that will run the motor
        self.job_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True  # Ensure it exits when the main thread exits
        self.worker_thread.start()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup([step_pin, dir_pin, enable_pin], GPIO.OUT)
        self.home()

    def _worker(self):
        # Continuously check for jobs in the queue
        while True:
            args = self.job_queue.get()  # Get the next job
            if args is None:  # Stop signal
                break
            self.do_steps(*args)
            self.job_queue.task_done()  # Signal that the job is done

    def home(self):
        self.do_steps_sync(Direction.clockwise, int(self.steps_per_rev / 4), 1)
        self.do_steps_sync(Direction.counter_clockwise,
                           int(self.steps_per_rev / 4), 1)

    def stop(self):
        # Stop the worker by adding a None job to signal shutdown
        self.job_queue.put(None)
        self.worker_thread.join()  # Wait for the thread to finish
        GPIO.output(self.enable_pin, GPIO.LOW)

    def move_to_sync(self, degrees=None, radians=None):
        target_rev = 0
        if degrees:
            target_rev = degrees / 360
        elif radians:
            target_rev = radians / (2*math.pi)

        target_position = target_rev * self.steps_per_rev
        steps = int(self.position - target_position)

        logger.debug(f"Current Position {self.position}\n"
                     f"Target Position {target_position}\n"
                     f"Taking {steps} steps")

        if steps > 0:
            self.do_steps_sync(
                Direction.counter_clockwise, steps, 0.1)
        else:
            self.do_steps_sync(
                Direction.clockwise, -steps, 0.1)

    def do_steps_sync(self, *args):
        self.job_queue.put(args)

    def do_steps(self, direction, step_count, delay_ms):
        if direction:
            self.position += step_count
        else:
            self.position -= step_count
        logger.debug(f"doing {step_count} steps. Direction {direction}")
        GPIO.output(self.enable_pin, GPIO.HIGH)
        GPIO.output(self.dir_pin, direction)
        delay_s = delay_ms/1000

        for i in range(step_count):
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.LOW)
