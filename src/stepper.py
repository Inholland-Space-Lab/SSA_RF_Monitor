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

# This class controls one stepper motor.
# Two instances are made in the Dish class in Dish._create_stepper, one for elevation, one for azimuth.
# Both instances are defined by this class, they contain the same methods (functions within a class)
# They have the same variables, but the variable values are unique to each instance.
# eg: both motors have a direction pin called dir_pin, but the value is different, as each motor has their own pin controlling direction


class Stepper():
    dir_pin: int  # Controls direction, set to high for clockwise, low for counter clockwise
    enable_pin: int  # Must be high to enable the stepper, set to low to disable
    gear_ratio: float  # Ratio of the gearbox. Used to convert angles to amount of steps
    # Microstepping setting of motordriver (see stepper driver datasheet). Is the amount of steps in one motor revolution, ignoring the gearbox
    resolution: int

    pwm: HardwarePWM  # Pulse Width Modulation library. Used to drive the step pin of the stepper driver at high and consistent rates

    # How long the pid controller should wait before updating again (in seconds)
    pid_delay = 0.0001
    # Callback function used to get the current position of the motor. Is set Dish._setup_motors.
    # Should return the axis of the position sensor that belongs to this motor
    position_callback: any

    # PID controller variables:
    pid: PID  # Instance of PID library
    do_pid: bool  # Must be true for the pid to be active. Used to cancel the timer of the pid controller. To enable/disable the pid, use the start_pid and stop_pid methods
    # maximum acceleration and velocity used to clamp the output of the pid controller to prevent it from spinning out of control
    max_acceleration: float  # steps per second^2
    max_velocity: float  # steps per second
    # current acceleration and velocity used by the pid controller
    acceleration: float  # steps per second^2
    velocity: float  # steps per second
    # Position that the pid controller tries to achieve
    goal: int  # steps

    # get the position indicated by the sensor using the position_callback defined in Dish._setup_motors
    @property
    def sensor_position(self):
        try:
            # call the callback
            pos = self.position_callback()

            if pos:
                return pos  # normal behavior
            else:
                return 0  # if the callback didn't work

        except Exception as e:  # If the callback crashed
            logger.warning(f"position callback not implemented!")
            logger.error(str(e))
            self.stop_pid()
            return 0

    # get the distance from the current position to the goal
    @property
    def distance(self) -> int:
        position = self.sensor_position / 360 * \
            self.steps_per_rev  # convert from degrees to steps
        # make the value between 0 and 360 degrees (in steps)
        distance = (self.goal - position) % self.steps_per_rev
        # make the value between -180 and 180 degrees (in steps)
        if distance > self.steps_per_rev / 2:
            distance -= self.steps_per_rev
        return distance

    # get the amount of steps required for one full revolution
    @property
    def steps_per_rev(self):
        return self.resolution * self.gear_ratio

    # Return a nice formatted string containing all the information when printing the class to the terminal or logs
    def __str__(self):
        return \
            f"a: {self.acceleration:.4f}\n" + \
            f"v: {self.velocity:.4f}\n" + \
            f"position: {self.sensor_position}\n" + \
            f"goal: {self.goal}\n" + \
            f"pid enabled: {self.do_pid}\n" + \
            f"pid tunings: {self.pid.tunings}\n" + \
            ""

    # This creates an instance of the stepper class. It is run in Dish._setup_motors as "Stepper()". Once for each motor
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
        # Transfer the arguments of this function to properties of the class
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.pwm = pwm
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([dir_pin, enable_pin], GPIO.OUT)  # configure pins as output

        # Motor properties
        self.gear_ratio = gear_ratio
        self.resolution = resolution

        # Setup the thread and queue that will run the motor.
        # The thread ensures that when the motor is waiting for its movement order to finish, it only blocks its own thread not the whole program.
        # The queue is the way of communicating between the main program and the thread
        self.job_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        # Ensure the thread also exits when the main program exits
        self.worker_thread.daemon = True
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

    # This is what the thread is doing
    def _worker(self):
        # Continuously check for jobs in the queue
        while True:
            args = self.job_queue.get()  # Get the next job
            if args is None:  # no arguments = Stop signal
                break
            self.do_steps(*args)  # move the motor with the args from the queue
            self.job_queue.task_done()  # Signal that the job is done

    # move the motor to "zero" position
    def zero(self):
        # Not implemented, not necessary yet
        pass

    # perform the homing sequence
    def home(self):
        # No end stops, so no homing sequence
        pass

    # Stop the motor. For during runtime, can start motor again. (might jerk the motor a bit)
    def stop(self):
        logger.debug("stopping motor")
        self.velocity = 0  # reset velocity for pid controller

        # stop the pwm controller
        self.pwm.change_frequency(1)  # frequency 0 hz is not allowed
        self.pwm.stop()

        # pull the enable pin low to disable the stepper
        GPIO.output(self.enable_pin, GPIO.LOW)

    # Disable the motor. Only when program exits, cannot start motor again
    def disable(self):
        self.stop_pid()  # stop the pid
        self.stop()  # stop the motor
        # remove the pin associations
        GPIO.cleanup([self.enable_pin, self.dir_pin])

    # Sets the pwm to the given speed, handles the direction pin for negative values.
    # Setting to zero velocity stops the motor without it jerking (the stop method does jerk)
    def _set_speed(self, velocity: float):
        # Check if the pwm is configured, skip if it isn't
        if self.pwm == None:
            logger.error("No pwm configured!")
            return

        logger.debug(f"Setting pwm: {velocity}")
        # Set enable pin high to enable the stepper
        GPIO.output(self.enable_pin, GPIO.HIGH)

        # Check if stopping, clockwise or counterclockwise
        if velocity == 0:
            self.pwm.stop()
        elif velocity > 1:  # pwm frequency cannot be lower than 1
            GPIO.output(self.dir_pin, GPIO.LOW)
            self.pwm.start(50)  # duty cycle of 50%
            self.pwm.change_frequency(velocity)
        elif velocity < -1:
            GPIO.output(self.dir_pin, GPIO.HIGH)
            self.pwm.start(50)
            self.pwm.change_frequency(-velocity)
        else:  # velocities between -1 and 1, and other values
            self.pwm.stop()

    # Do a specific amount of steps without pid control. Negative steps for other direction
    def do_steps(self, step_count, velocity=1000, *args):
        # check if pid is running
        if self.do_pid:
            logger.warning(
                f"Trying to do steps while pid is active, ignoring step command")
            return
        duration = abs(step_count/velocity)  # calculate the time required

        logger.debug(f"Doing {step_count} steps. Will take {duration} seconds")
        GPIO.output(self.enable_pin, GPIO.HIGH)  # enable the stepper

        if step_count > 0:  # set the velocity to have the same sign as the step count
            velocity = abs(velocity)
        else:
            velocity = -abs(velocity)

        # perform the movement:
        self._set_speed(velocity)
        time.sleep(duration)
        self._set_speed(0)

    # do_steps, but ordered to the thread instead of the main program
    def do_steps_sync(self, *args):
        self.job_queue.put(args)

    # Move a specific angle in degrees or radians. It converts to steps and then calls do_steps
    def move_angle(self, degrees=None, radians=None):
        # convert to revolutions
        rev = 0
        if degrees:
            rev = degrees / 360
        elif radians:
            rev = radians / (2*math.pi)

        steps = rev * self.steps_per_rev  # convert to amount of steps
        self.do_steps(steps)  # call do_steps
        duration = steps * 1000
        return duration  # return amount of time required (used for testing)

    # move_angle, but calls do_steps_sync
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

    # configue the tuning values of the pid controller
    def tune(self, p, i, d):
        self.pid.Kp = p
        self.pid.Ki = i
        self.pid.Kd = d

    # Set the target of the pid controller in degrees or radians
    def set_target(self, degrees=None, radians=None):
        # convert to revolutions
        target_rev = 0
        if degrees:
            target_rev = degrees / 360
        elif radians:
            target_rev = radians / (2*math.pi)

        # convert to steps and set pid goal
        self.goal = target_rev * self.steps_per_rev

    # start the pid controller
    def start_pid(self):
        # set the last time to now. prevents the pid from doing a huge timestep
        self._last_time = time.monotonic()
        self.do_pid = True
        self._calc_pid()  # start the pid cycle (_calc_pid calls itself after pid_delay)

    # Stop the pid controller
    def stop_pid(self):
        self.stop()  # stop the motor
        self._last_time = 0  # reset the time used for dt calculation
        # do_pid is checked every time in the _calc_pid cycle. Setting to false stops the cycle
        self.do_pid = False

    # Calculates and sets the current velocity using the pid controller
    def _calc_pid(self):
        # Check if pid is supposed to be running
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
                            min(self.max_velocity, self.velocity))  # clamp the velocity
        logger.debug(f"calc pid: {self.velocity}"
                     f"dt: {dt}")
        # set the speed of the motor to calculated value
        self._set_speed(self.velocity)

        # Run again after pid_delay. Runs in separate thread to not block main program
        timer = threading.Timer(
            self.pid_delay,
            self._calc_pid)
        timer.daemon = True  # Makes sure the timer stops when the process ends/crashes
        timer.start()
