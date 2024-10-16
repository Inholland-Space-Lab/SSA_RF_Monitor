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

    def __init__(self, step_pin, dir_pin, enable_pin):
        # Define Pins
        logger.info("Creating Stepper")
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin

        # Setup the thread and queue that will run the motor
        self.job_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True  # Ensure it exits when the main thread exits
        self.worker_thread.start()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup([step_pin, dir_pin, enable_pin], GPIO.OUT)

    def _worker(self):
        # Continuously check for jobs in the queue
        while True:
            args = self.job_queue.get()  # Get the next job
            if args is None:  # Stop signal
                break
            self.do_steps(*args)
            self.job_queue.task_done()  # Signal that the job is done

    def stop(self):
        # Stop the worker by adding a None job to signal shutdown
        self.job_queue.put(None)
        self.worker_thread.join()  # Wait for the thread to finish
        GPIO.output(self.enable_pin, GPIO.LOW)

    def do_steps_sync(self, *args):
        self.job_queue.put(args)

    def do_steps(self, direction, step_count, delay_ms):
        logger.debug(f"doing {step_count} steps. Direction {direction}")
        GPIO.output(self.enable_pin, GPIO.HIGH)
        GPIO.output(self.dir_pin, direction)
        delay_s = delay_ms/1000

        for i in range(step_count):
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.LOW)
