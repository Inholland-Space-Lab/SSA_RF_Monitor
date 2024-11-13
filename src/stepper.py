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
    # step_pin: int
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

    @property
    def sensor_position(self):
        try:
            return self.position_callback()
        except:
            logger.warning(f"position callback not implemented!")
            self.stop_pid()
            return 0

    @property
    def distance(self) -> int:
        position = self.sensor_position / 360 * self.steps_per_rev
        distance = (self.goal - position) % self.steps_per_rev
        if distance > self.steps_per_rev / 2:
            distance -= self.steps_per_rev
        return distance

    @property
    def steps_per_rev(self):
        return self.resolution * self.gear_ratio

    def __init__(
        self,
        # step_pin,
        dir_pin,
        enable_pin,
        pwm,
        position_callback,
        resolution=3200,
        gear_ratio=(19+(38/187)),
    ):
        # Define Pins
        logger.info("Creating Stepper")
        # self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.gear_ratio = gear_ratio
        self.resolution = resolution
        # self.position = 0
        self.pwm = pwm
        self.do_pid = False

        # Setup the thread and queue that will run the motor
        self.job_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True  # Ensure it exits when the main thread exits
        self.worker_thread.start()

        self.max_acceleration = 2000
        self.max_velocity = 100000
        self.position_callback = position_callback
        # self.sensor = sensor
        self.velocity = 0
        self.goal = 0
        self.distance_sum = 0
        self._last_time = 0
        self.pid = PID(0, 0, 0, sample_time=None,
                       output_limits=(-self.max_acceleration, self.max_acceleration))

        GPIO.setmode(GPIO.BCM)
        GPIO.setup([dir_pin, enable_pin], GPIO.OUT)
        # self.home()

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
        # self.position = 0
        pass

    def home(self):
        self.do_steps_sync(int(self.steps_per_rev / 4))
        self.do_steps_sync(-int(self.steps_per_rev / 4))

    def stop(self):
        self.stop_pid()
        self.pwm.change_frequency(1)
        self.pwm.stop()
        GPIO.output(self.enable_pin, GPIO.LOW)
        GPIO.cleanup([self.enable_pin, self.dir_pin])

    def _set_speed(self, velocity: float):
        """Set the step pin to pulse at the specified frequency."""
        if self.pwm == None:
            logger.error("No pwm configured!")
            return
        logger.debug(f"Setting pwm: {velocity}")
        GPIO.output(self.enable_pin, GPIO.HIGH)
        if velocity == 0:
            self.pwm.stop()  # Stop the motor
        elif velocity > 1:
            GPIO.output(self.dir_pin, GPIO.LOW)
            self.pwm.start(50)
            self.pwm.change_frequency(velocity)
        elif velocity < -1:
            GPIO.output(self.dir_pin, GPIO.HIGH)
            self.pwm.start(50)
            self.pwm.change_frequency(-velocity)
        else:
            self.pwm.stop()  # Stop the motor

    def do_steps_sync(self, *args):
        self.job_queue.put(args)

    def do_steps(self, step_count, velocity=500, *args):
        if self.do_pid:
            logger.warning(
                f"Trying to do steps while pid is active, ignoring step command")
            return

        logger.debug(f"doing {step_count} steps")
        GPIO.output(self.enable_pin, GPIO.HIGH)
        # self.position += step_count
        if step_count > 0:
            GPIO.output(self.dir_pin, GPIO.LOW)
        else:
            GPIO.output(self.dir_pin, GPIO.HIGH)

        self._set_speed(velocity)
        time.sleep(step_count/velocity)
        self._set_speed(0)

    def move_angle(self, degrees=None, radians=None):
        rev = 0
        if degrees:
            rev = degrees / 360
        elif radians:
            rev = radians / (2*math.pi)

        steps = rev * self.steps_per_rev
        self.do_steps_sync(steps)

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
        self._last_time = 0
        self.do_pid = True
        self._calc_pid()

    def stop_pid(self):
        self._last_time = 0
        self.do_pid = False

    def _calc_pid(self):
        if not self.do_pid:
            return
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
        self._set_speed(self.velocity)

        (p, i, d) = self.pid.components
        # (yaw, roll, pitch) = self.sensor.euler
        # sys, gyro, accel, mag = self.sensor.calibration_status

        # logger.debug(
        #     f"{(UP+CLR)*18}"
        #     f"{'-'*40}\n"
        #     f"dt: {dt:.4f}\n"
        #     f"p: {p:.4f}\n"
        #     f"i: {i:.4f}\n"
        #     f"d: {d:.4f}\n"
        #     f"a: {self.acceleration:.4f}\n"
        #     f"v: {self.velocity:.4f}\n"
        #     # f"yaw: {yaw:.0f}\n"
        #     # f"pitch: {pitch:.0f}\n"
        #     # f"roll: {roll:.0f}\n"
        #     # f"sys: {sys:.0f}\n"
        #     # f"gyro: {gyro:.0f}\n"
        #     # f"accel: {accel:.0f}\n"
        #     # f"mag: {mag:.0f}\n"
        #     f"goal: {self.goal:.0f}\n"
        #     f"distance: {self.distance:.0f}\n"
        #     f"out of: {ControlledStepper.max_delay}"
        # )

        timer = threading.Timer(
            Stepper.pid_delay,
            self._calc_pid)
        timer.daemon = True  # Makes sure the timer stops when the process crashes
        timer.start()


class ControlledStepper(Stepper):

    max_delay = 0.0001  # seconds
    p = 0
    i = 0
    d = 0
    # sensor: BNO055_I2C
    position_callback: any

    pid: PID
    do_pid: bool
    max_acceleration: float  # steps per second^2
    max_velocity: float  # steps per second
    velocity: float  # steps per second
    acceleration: float  # steps per second^2
    goal: int  # steps
    distance_sum: float  # steps

    @property
    def sensor_position(self):
        return self.position_callback()

    @property
    def distance(self) -> int:
        position = self.sensor_position / 360 * self.steps_per_rev
        distance = (self.goal - position) % self.steps_per_rev
        if distance > self.steps_per_rev / 2:
            distance -= self.steps_per_rev
        return distance

    def __init__(self, step_pin, dir_pin, enable_pin,
                 resolution=3200, gear_ratio=None,
                 max_speed=100000, max_acceleration=2000,
                 sensor=None, pwm=None,
                 position_callback=None):
        super().__init__(step_pin, dir_pin, enable_pin, resolution, pwm=pwm)
        self.max_acceleration = max_acceleration
        self.max_velocity = max_speed
        self.position_callback = position_callback
        # self.sensor = sensor
        self.velocity = 0
        self.goal = 0
        self.distance_sum = 0
        self._last_time = 0
        self.pid = PID(0, 0, 0, sample_time=None,
                       output_limits=(-max_acceleration, max_acceleration))
        logger.debug("init succesful")
        logger.debug("\n" * 8)
        # (yaw, roll, pitch) = self.sensor.euler
        # self.move_to_sync(degrees=yaw)
        self.do_pid = True
        self._calc_pid()

    def home(self):
        pass

    def zero(self):
        super().zero()
        self.velocity = 0
        self.distance_sum = 0
        self.pid._integral = 0

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

    def _calc_pid(self):
        if not self.do_pid:
            return
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
        self._set_speed(self.velocity)

        (p, i, d) = self.pid.components
        # (yaw, roll, pitch) = self.sensor.euler
        # sys, gyro, accel, mag = self.sensor.calibration_status

        logger.debug(
            f"{(UP+CLR)*18}"
            f"{'-'*40}\n"
            f"dt: {dt:.4f}\n"
            f"p: {p:.4f}\n"
            f"i: {i:.4f}\n"
            f"d: {d:.4f}\n"
            f"a: {self.acceleration:.4f}\n"
            f"v: {self.velocity:.4f}\n"
            # f"yaw: {yaw:.0f}\n"
            # f"pitch: {pitch:.0f}\n"
            # f"roll: {roll:.0f}\n"
            # f"sys: {sys:.0f}\n"
            # f"gyro: {gyro:.0f}\n"
            # f"accel: {accel:.0f}\n"
            # f"mag: {mag:.0f}\n"
            f"goal: {self.goal:.0f}\n"
            f"distance: {self.distance:.0f}\n"
            f"out of: {ControlledStepper.max_delay}"
        )

        timer = threading.Timer(
            ControlledStepper.max_delay,
            self._calc_pid)
        timer.daemon = True  # Makes sure the timer stops when the process crashes
        timer.start()

    def on_task_done(self, *args):
        do_pid = args[2]
        if do_pid:
            self._calc_pid()
