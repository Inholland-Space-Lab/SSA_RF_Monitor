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


class StepMode():
    linear = 0
    exp = 1


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
        self.do_steps_sync(Direction.clockwise, int(self.steps_per_rev / 4))
        self.do_steps_sync(Direction.counter_clockwise,
                           int(self.steps_per_rev / 4))

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

        self.do_steps_sync(steps, 2)
        # if steps > 0:
        #     self.do_steps_sync(
        #         Direction.counter_clockwise, steps, 2)
        # else:
        #     self.do_steps_sync(
        #         Direction.clockwise, -steps, 2)

    def do_steps_sync(self, *args):
        # logger.debug("do_steps_sync")
        self.job_queue.put(args)

    def do_steps(self, step_count, delay_ms=0.1):
        # direction

        # if direction:
        #     self.position += step_count
        # else:
        #     self.position -= step_count
        logger.debug(f"doing {step_count} steps")
        GPIO.output(self.enable_pin, GPIO.HIGH)
        if step_count > 0:
            self.position += step_count
            GPIO.output(self.dir_pin, GPIO.LOW)
        else:
            self.position -= step_count
            GPIO.output(self.dir_pin, GPIO.HIGH)

        delay_s = delay_ms/1000

        for i in range(step_count):
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay_s)
            GPIO.output(self.step_pin, GPIO.LOW)

    def do_steps_exp(self, step_count, total_time=None):
        if step_count == 0:
            return
        # if direction:
        #     self.position += step_count
        # else:
        #     self.position -= step_count
        GPIO.output(self.enable_pin, GPIO.HIGH)
        # GPIO.output(self.dir_pin, direction)

        if step_count > 0:
            self.position += step_count
            GPIO.output(self.dir_pin, GPIO.LOW)
        else:
            self.position -= step_count
            GPIO.output(self.dir_pin, GPIO.HIGH)

        if not total_time:
            total_time = step_count / 10000

        logger.debug(
            f"doing {step_count} steps in {total_time} seconds")

        avg_delay = total_time/step_count
        a = 2/step_count

        def delay(step):
            x = step * avg_delay
            if step < step_count/2:
                return -(a * x) + (1.5 * avg_delay)
            else:
                return (a*x) - (0.5 * avg_delay)

        logger.debug(f"average delay: {avg_delay}"
                     f"from {delay(0)} to {delay(step_count/2)}")
        starting_time = time.time()

        for i in range(step_count):
            # logger.debug(f"delay {str(delay(i))}")
            time.sleep(delay(i))
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay(i))
            GPIO.output(self.step_pin, GPIO.LOW)

        logger.debug(f"took {time.time() - starting_time} seconds")


class ControlledStepper(Stepper):

    step_length = 0.001
    p = 0.1
    i = 0
    d = 0.9

    max_acceleration: float
    max_velocity: float
    velocity: float
    goal: int
    distance_sum: float

    @property
    def distance(self) -> int:
        return self.goal - self.position

    def __init__(self, step_pin, dir_pin, enable_pin, resolution=None, gear_ratio=None, max_speed=1000000):
        super().__init__(step_pin, dir_pin, enable_pin)
        # self.max_acceleration = max_acceleration
        self.max_velocity = max_speed
        self.velocity = 0
        self.goal = 0
        self.distance_sum = 0
        logger.debug("init succesful")
        self.calc_steps()

    def move_to_sync(self, degrees=None, radians=None):
        target_rev = 0
        if degrees:
            target_rev = degrees / 360
        elif radians:
            target_rev = radians / (2*math.pi)

        self.goal = target_rev * self.steps_per_rev

    def controller(self):
        # PID
        pid = 0

        # logger.debug("controller")
        logger.debug(
            f"\033[F\033[Kposition: {self.position}\n"
            f"\033[F\033[Kgoal: {self.goal}\n"
            f"\033[F\033[Kdistance: {self.distance}"
        )

        # P
        pid += ControlledStepper.p * self.distance

        # I
        pid += ControlledStepper.i * self.distance_sum
        self.distance_sum += self.distance

        # D
        pid += ControlledStepper.d * self.velocity
        logger.debug(f"\033[F\033[Kpid: {pid}")

        target_velocity = max(-self.max_velocity, min(self.max_velocity, pid))

        logger.debug(
            f"\033[F\033[KVelocity: {target_velocity}\n"
            f"\033[F\033[KAcceleration: {abs(self.velocity - target_velocity)}")
        return target_velocity

    def calc_steps(self):
        self.velocity = self.controller()
        step_delay = ControlledStepper.step_length
        if not (self.velocity == 0):
            step_delay = min(ControlledStepper.step_length,
                             abs(1 / self.velocity))

        steps = math.floor(self.velocity * ControlledStepper.step_length)
        logger.debug(f"\033[F\033[Kcalc steps: {steps}, delay: {step_delay}")
        self.do_steps_sync(steps, step_delay)

        timer = threading.Timer(ControlledStepper.step_length, self.calc_steps)
        timer.daemon = True
        timer.start()
