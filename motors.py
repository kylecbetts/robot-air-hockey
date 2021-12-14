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
RIGHT = (1, 1)
LEFT = (0, 0)

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

# Strategy Globals
MAX_FREQ = 500
MIN_FREQ = 5
accel_ramp = 0.1
linear_accel_ramp=5

# PWM
freq = MIN_FREQ # Motors always at same speed
pwm1 = GPIO.PWM(STEP_1, freq)
pwm2 = GPIO.PWM(STEP_2, freq)

def slow_to_stop():
    global freq
    while freq > MIN_FREQ:
        freq -= freq*accel_ramp
        #freq -= linear_accel_ramp
    #Stop
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)



# Slow down frequency and saturate at 0
def slow_down():
    global freq
    
    if freq > MIN_FREQ:
        freq -= freq*accel_ramp
        #freq -= linear_accel_ramp
    else:
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
    else:
        freq = MAX_FREQ

    # Change frequency
    pwm1.ChangeFrequency(freq)
    pwm2.ChangeFrequency(freq)

# Update PWM Parameters
def update_motors(msg):
    print(freq)
    if (msg == "STOP"):
        slow_down()
    elif (msg == "LEFT"): 
        if GPIO.input(DIR_1) == LEFT[0]:
            speed_up()
        else:
            slow_down()
            # Change Direction
            if freq <= MIN_FREQ:
                GPIO.output(DIR_PINS, LEFT)
    elif (msg == "RIGHT"): 
        if GPIO.input(DIR_1) == RIGHT[0]:
            speed_up()
        else:
            slow_down()
            # Change Direction
            if freq <= MIN_FREQ:
                GPIO.output(DIR_PINS, RIGHT)
            
def terminate_motors():
    global done
    print("terminating motors")
    slow_to_stop()
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
            terminate_motors()
        else:
            update_motors(msg[1])
            print(msg)
