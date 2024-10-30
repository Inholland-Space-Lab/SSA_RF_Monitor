import math
import threading
import queue
import logging
import multiprocessing
import time
from simple_pid import PID
from config import Config
from RPi import GPIO

logger = logging.getLogger(__name__)

UP = "\033[F"
CLR = "\033[K"


def line(i):
    return UP*i + CLR


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
            self.on_task_done(*args)

    def on_task_done(self, *args):
        pass

    def zero(self):
        self.position = 0

    def home(self):
        self.do_steps_sync(int(self.steps_per_rev / 4))
        self.do_steps_sync(-int(self.steps_per_rev / 4))

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

        self.do_steps_sync(steps)
        # if steps > 0:
        #     self.do_steps_sync(
        #         Direction.counter_clockwise, steps, 2)
        # else:
        #     self.do_steps_sync(
        #         Direction.clockwise, -steps, 2)

    def do_steps_sync(self, *args):
        # logger.debug("do_steps_sync")
        self.job_queue.put(args)

    def do_steps(self, step_count, delay_ms=0.1, *args):
        # direction

        # if direction:
        #     self.position += step_count
        # else:
        #     self.position -= step_count
        logger.debug(f"doing {step_count} steps")
        GPIO.output(self.enable_pin, GPIO.HIGH)
        self.position += step_count
        if step_count > 0:
            GPIO.output(self.dir_pin, GPIO.LOW)
        else:
            GPIO.output(self.dir_pin, GPIO.HIGH)

        delay_s = delay_ms/1000

        for i in range(abs(step_count)):
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

        self.position += step_count
        if step_count > 0:
            GPIO.output(self.dir_pin, GPIO.LOW)
        else:
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

    max_delay = 1000.0  # milliseconds
    p = 0.000005
    i = 0
    d = 0.001

    pid: PID
    max_acceleration: float  # steps per second^2
    max_velocity: float  # steps per second
    velocity: float  # steps per second
    acceleration: float  # steps per second^2
    goal: int  # steps
    distance_sum: float  # steps

    @property
    def distance(self) -> int:
        return self.goal - self.position

    def __init__(self, step_pin, dir_pin, enable_pin, resolution=None, gear_ratio=None, max_speed=1E12, max_acceleration=1E12):
        super().__init__(step_pin, dir_pin, enable_pin)
        self.max_acceleration = max_acceleration
        self.max_velocity = max_speed
        self.velocity = 0
        self.goal = 0
        self.distance_sum = 0
        self._last_time = 0
        self.pid = PID(0.000005, 0, 0.001, sample_time=None)
        logger.debug("init succesful")
        logger.debug("\n" * 8)
        self.calc_steps()

    def home(self):
        pass

    def zero(self):
        super().zero()
        self.velocity = 0
        self.distance_sum = 0

    def tune(self, p, i, d):
        self.pid.Kp = p
        self.pid.Ki = i
        self.pid.Kd = d

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

        # P
        pid += ControlledStepper.p * self.distance

        # I
        self.distance_sum += self.distance * ControlledStepper.max_delay
        pid += ControlledStepper.i * self.distance_sum

        # D
        pid -= ControlledStepper.d * self.distance / ControlledStepper.max_delay

        pid = max(-self.max_acceleration, min(self.max_acceleration, pid))

        # logger.debug(
        #     f"{(UP+CLR)*11}"
        #     f"p: {ControlledStepper.p}\n"
        #     f"i: {ControlledStepper.i}\n"
        #     f"d: {ControlledStepper.d}\n"
        #     f"position: {self.position}\n"
        #     f"goal: {self.goal}\n"
        #     f"distance: {self.distance}\n"
        #     f"pid: {pid}"
        # )

        return pid

    def calc_steps(self):
        # update time
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        # update dynamics
        self.acceleration = self.pid(self.distance)
        self.pid.sample_time
        self.velocity += self.acceleration * dt
        self.velocity = max(-self.max_velocity,
                            min(self.max_velocity, self.velocity))

        # get delay between steps for this velocity
        step_delay = ControlledStepper.max_delay
        if not (self.velocity == 0):
            step_delay = min(ControlledStepper.max_delay,
                             abs(1 / self.velocity))

        # do a step with that delay
        if step_delay >= ControlledStepper.max_delay:
            self.do_steps_sync(1, step_delay, True)
        else:
            # for low velocities step delay can get very high,
            # do no step and calculate again after max_delay
            # to avoid stalling the steppers
            self.do_steps_sync(0, step_delay, True)

        logger.debug(
            f"{(UP+CLR)*7}"
            f"a: {self.acceleration:.4f}\n"
            f"v: {self.velocity:.4f}\n"
            f"p: {self.position:.0f}\n"
            f"goal: {self.goal:.0f}\n"
            f"distance: {self.distance:.0f}\n"
            f"delay: {step_delay:.0f}, "
            f"out of: {ControlledStepper.max_delay}"
        )

    def on_task_done(self, *args):
        do_pid = args[2]
        if do_pid:
            self.calc_steps()
