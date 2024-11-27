import math
import threading
import queue
import logging
import multiprocessing
import time
from adafruit_bno055 import BNO055_I2C
from simple_pid import PID
from config import Config
from RPi import GPIO
from rpi_hardware_pwm import HardwarePWM

logger = logging.getLogger(__name__)

UP = "\033[F"
CLR = "\033[K"


def line(i):
    return UP*i + CLR


class Stepper():
    dir_pin: int
    enable_pin: int
    # position: int
    gear_ratio: float
    resolution: int

    pwm: HardwarePWM

    pid_delay = 0.0001  # seconds
    position_callback: any

    pid: PID
    do_pid: bool
    max_acceleration: float  # steps per second^2
    max_velocity: float  # steps per second
    velocity: float  # steps per second
    acceleration: float  # steps per second^2
    goal: int  # steps

    # get the position indicated by the sensor using the position_callback defined in Dish._setup_motors
    @property
    def sensor_position(self):
        try:
            pos = self.position_callback()
            if pos:
                return pos
            else:
                return 0
        except Exception as e:
            logger.warning(f"position callback not implemented!")
            logger.error(str(e))
            # self.stop_pid()
            return 0

    # get the distance from the current position to the goal
    @property
    def distance(self) -> int:
        position = self.sensor_position / 360 * self.steps_per_rev
        distance = (self.goal - position) % self.steps_per_rev
        if distance > self.steps_per_rev / 2:
            distance -= self.steps_per_rev
        return distance

    # get the amount of steps required for one full revolution
    @property
    def steps_per_rev(self):
        return self.resolution * self.gear_ratio

    #
    def __str__(self):
        return \
            f"a: {self.acceleration:.4f}\n" + \
            f"v: {self.velocity:.4f}\n" + \
            f"position: {self.sensor_position}\n" + \
            f"goal: {self.goal}\n" + \
            f"pid enabled: {self.do_pid}\n" + \
            f"pid tunings: {self.pid.tunings}\n" + \
            ""

    def __init__(
        self,
        dir_pin,
        enable_pin,
        pwm,
        position_callback,
        resolution=3200,
        gear_ratio=(19+(38/187)),
    ):
        logger.info("Creating Stepper")

        # Define Pins
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.pwm = pwm
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([dir_pin, enable_pin], GPIO.OUT)

        # Motor properties
        self.gear_ratio = gear_ratio
        self.resolution = resolution

        # Setup the thread and queue that will run the motor
        self.job_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True  # Ensure it exits when the main thread exits
        self.worker_thread.start()

        # Setup PID properties
        self.do_pid = False
        self.max_acceleration = 2000
        self.max_velocity = 100000
        self.position_callback = position_callback
        self.acceleration = 0
        self.velocity = 0
        self.goal = 0
        self.distance_sum = 0
        self._last_time = 0
        self.pid = PID(0, 0, 0, sample_time=None,
                       output_limits=(-self.max_acceleration, self.max_acceleration))

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
        pass

    def home(self):
        pass
        # self.do_steps_sync(int(self.steps_per_rev / 4))
        # self.do_steps_sync(-int(self.steps_per_rev / 4))

    def stop(self):
        logger.debug("stopping motor")
        self.velocity = 0
        self.pwm.change_frequency(1)
        self.pwm.stop()
        GPIO.output(self.enable_pin, GPIO.LOW)

    def disable(self):
        self.stop_pid()
        self.stop()
        GPIO.cleanup([self.enable_pin, self.dir_pin])

    def _set_speed(self, velocity: float):
        if self.pwm == None:
            logger.error("No pwm configured!")
            return

        logger.debug(f"Setting pwm: {velocity}")
        GPIO.output(self.enable_pin, GPIO.HIGH)

        if velocity == 0:
            self.pwm.stop()
        elif velocity > 1:
            GPIO.output(self.dir_pin, GPIO.LOW)
            self.pwm.start(50)
            self.pwm.change_frequency(velocity)
        elif velocity < -1:
            GPIO.output(self.dir_pin, GPIO.HIGH)
            self.pwm.start(50)
            self.pwm.change_frequency(-velocity)
        else:
            self.pwm.stop()

    def do_steps_sync(self, *args):
        self.job_queue.put(args)

    def do_steps(self, step_count, velocity=1000, *args):
        if self.do_pid:
            logger.warning(
                f"Trying to do steps while pid is active, ignoring step command")
            return
        duration = abs(step_count/velocity)

        logger.debug(f"Doing {step_count} steps. Will take {duration} seconds")
        GPIO.output(self.enable_pin, GPIO.HIGH)

        if step_count > 0:
            velocity = abs(velocity)
        else:
            velocity = -abs(velocity)

        self._set_speed(velocity)
        time.sleep(duration)
        self._set_speed(0)

    def move_angle(self, degrees=None, radians=None):
        rev = 0
        if degrees:
            rev = degrees / 360
        elif radians:
            rev = radians / (2*math.pi)

        steps = rev * self.steps_per_rev
        self.do_steps(steps)
        duration = steps * 1000
        return duration

    def move_angle_sync(self, degrees=None, radians=None):
        rev = 0
        if degrees:
            rev = degrees / 360
        elif radians:
            rev = radians / (2*math.pi)

        steps = rev * self.steps_per_rev
        self.do_steps_sync(steps)
        duration = steps * 1000
        return duration

    def tune(self, p, i, d):
        self.pid.Kp = p
        self.pid.Ki = i
        self.pid.Kd = d

    def set_target(self, degrees=None, radians=None):
        target_rev = 0
        if degrees:
            target_rev = degrees / 360
        elif radians:
            target_rev = radians / (2*math.pi)

        self.goal = target_rev * self.steps_per_rev

    def start_pid(self):
        self._last_time = time.monotonic()
        self.do_pid = True
        self._calc_pid()

    def stop_pid(self):
        self.stop()
        self._last_time = 0
        self.do_pid = False

    def _calc_pid(self):
        if not self.do_pid:
            logger.debug("PID DISABLED")
            return

        # update time
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        # update dynamics
        self.acceleration = self.pid(self.distance)  # pid calculation
        self.velocity += self.acceleration * dt
        self.velocity = max(-self.max_velocity,
                            min(self.max_velocity, self.velocity))
        logger.debug(f"calc pid: {self.velocity}"
                     f"dt: {dt}")
        self._set_speed(self.velocity)

        # Run again after pid_delay
        timer = threading.Timer(
            self.pid_delay,
            self._calc_pid)
        timer.daemon = True  # Makes sure the timer stops when the process ends/crashes
        timer.start()
