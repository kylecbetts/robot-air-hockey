'''
motors.py program
'''

import time
import RPi.GPIO as GPIO
from multiprocessing import Process, Pipe

# GPIO pin numbers
STEP_1 = 20
DIR_1 = 21
STEP_2 = 19
DIR_2 = 26

DIR_PINS = (DIR_1, DIR_2)
LEFT = (1, 1)
RIGHT = (0, 0)

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Initialize pins
GPIO.setup(DIR_1, GPIO.OUT)
GPIO.setup(STEP_1, GPIO.OUT)
GPIO.setup(DIR_2, GPIO.OUT)
GPIO.setup(STEP_2, GPIO.OUT)

# Connection Globals
strategy_conn = 0
done = 0

prev_t = 0
t = 0

# Strategy Globals
CM_TO_STEPS = 320
MAX_FREQ = 22000
MIN_FREQ = 40
accel_ramp = 0.1
linear_accel_ramp=2000

# PWM
freq = MIN_FREQ # Motors always at same speed
pwm1 = GPIO.PWM(STEP_1, freq)
pwm2 = GPIO.PWM(STEP_2, freq)

def slow_to_stop():
    global freq
    while freq > MIN_FREQ:
        #freq -= freq*accel_ramp
        freq -= linear_accel_ramp
    #Stop
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)



# Slow down frequency and saturate at 0
def slow_down():
    global freq
    
    if freq > MIN_FREQ:
        #freq -= freq*accel_ramp
        freq -= linear_accel_ramp
    
    if freq <= MIN_FREQ:
        freq = MIN_FREQ
        #Stop
        pwm1.ChangeDutyCycle(0)
        pwm2.ChangeDutyCycle(0)
   
    # Change frequency
    pwm1.ChangeFrequency(freq)
    pwm2.ChangeFrequency(freq)

# Speed up frequency and saturate at max
def speed_up():
    global freq

    if freq <= MIN_FREQ:
        #Start
        pwm1.ChangeDutyCycle(50)
        pwm2.ChangeDutyCycle(50)

    if freq < MAX_FREQ:
        #freq += freq*accel_ramp
        freq += linear_accel_ramp
    
    if freq > MAX_FREQ:
        freq = MAX_FREQ

    # Change frequency
    pwm1.ChangeFrequency(freq)
    pwm2.ChangeFrequency(freq)

# Update PWM Parameters
def update_motors(x_targ_dist, y_targ_dist):
    #global prev_t
    #global t
    #prev_t = t
    #t = time.time()
    msg = ""
    
    print("M - freq: {}".format(freq))

    # Window to decelerate
    # fps is about 30 so factor of 30 necessary for deceleration ramp,
    # which is in steps per second per interval
    decel_window = freq**2 / (2*linear_accel_ramp*30*CM_TO_STEPS)
    decel_window = abs(decel_window)

    #print("M - dec: {}".format(decel_window))
    #print("M - ytd: {}".format(y_targ_dist))

    # Determine direction motor needs to move
    if y_targ_dist < 0:
        msg = "RIGHT"
    elif y_targ_dist > 0:
        msg = "LEFT"
    else:
        msg = "STOP"

    # If you're going in the right direction, speed up
    # Unless you're within the distance it takes to decelerate to 0 at desired point
    # which is speed^2 / (2*accel*320)
    # If you're going in the wrong direction, slow down til you can change direction
    if (msg == "STOP"):
        #print("STOP")
        slow_down()
    elif (msg == "LEFT"):
        # If going in the right direction
        if GPIO.input(DIR_1) == LEFT[0]:
            # Slow down if close to target position
            if abs(y_targ_dist) <= decel_window:
                #print("L: SLOW")
                slow_down()
            else:
                #print("L: UP")
                speed_up()
        # Going in wrong direction
        else:
            #print("L: BACK")
            slow_down()
            if freq <= MIN_FREQ:
                GPIO.output(DIR_PINS, LEFT)
    elif (msg == "RIGHT"): 
        # Going in the right direction
        if GPIO.input(DIR_1) == RIGHT[0]:
            if abs(y_targ_dist) <= decel_window:
                #print("R: SLOW")
                slow_down()
            else:
                #print("R: UP")
                speed_up()
        # Going in wrong direction
        else:
            #print("R: BACK")
            slow_down()
            if freq <= MIN_FREQ:
                GPIO.output(DIR_PINS, RIGHT)
            
def terminate_motors():
    global done
    print("terminating motors")
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
    done = 1


def motors(conn):
    global strategy_conn
    strategy_conn = conn
    
    # Set Dir pins to logic low
    GPIO.output(DIR_PINS, GPIO.LOW)

    # start pwms
    pwm1.start(0)
    pwm2.start(0)

    # Inform strategy that process initialized successfully
    strategy_conn.send([1, True])

    while(not done):
        msg = strategy_conn.recv()
        if msg[0] == 0:
            pwm1.stop()
            pwm2.stop()
            terminate_motors()
        elif msg[0] == 2:
            print("Stop Message")
            slow_down()
            pwm1.stop()
            pwm2.stop()
        else:
            update_motors(msg[1], msg[2])
