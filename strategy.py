'''
strategy.py program
'''
from multiprocessing import Process, Pipe
from motors import motors
import math

# Connection Globals
vision_conn = 0
motors_conn = 0
motors_p = 0

# Table Globals
TABLE_HEIGHT = 48.0
TABLE_WIDTH = 98.0
ROBOT_SIDE_WIDTH = 49.0
DEFENCE_POSITION = (93.0, 24.0) 
TABLE_PADDING = 5.0

# Puck Globals
puck_x = 49.0
puck_y = 24.0
puck_x_last = 49.0
puck_y_last = 24.0
puck_speed_x = 0
puck_speed_y = 0
puck_missing = True
puck_missing_counter = 0

# Robot Globals
defence_position = 0
robot_x = 0
robot_y = 0
robot_x_target = 90.0
robot_y_target = 24.0
robot_y_desired = 0
robot_collision_time = 0
robot_missing = True

# Motor Constants
x_targ_dist = 0
y_targ_dist = 0


def update_puck_speed():
    global puck_speed_x, puck_speed_y
    if not puck_missing:
        delta_x = puck_x - puck_x_last
        delta_y = puck_y - puck_y_last
        puck_speed_x = delta_x * 30
        puck_speed_y = delta_y * 30
    

def update_locations(msg):
    global puck_x, puck_y, puck_x_last, puck_y_last, puck_missing, puck_missing_counter
    global robot_x, robot_y, robot_missing
    # If puck was found
    if msg[1] != -1:
        puck_missing = False
        puck_missing_counter = 0
        puck_x_last = puck_x
        puck_y_last = puck_y
        puck_x = msg[1]
        puck_y = msg[2]
    # If puck not found
    else:
        puck_missing = True
        puck_missing_counter += 1
    # If robot was found
    if msg[3] != -1:
        robot_x = msg[3]
        robot_y = msg[4]


def initialize_motors_process():
    global motors_conn, motors_p
    motors_conn, child_conn = Pipe()
    motors_p = Process(target=motors, args=(child_conn,))
    motors_p.start()
    # Wait for motors process to initialize
    motors_init = motors_conn.recv()
    if not (motors_init[0] == 1 and motors_init[1]):
        print("Failed to initialize motors.")
        terminate_strategy()


def terminate_strategy():
    print("Strategy terminating.")
    motors_conn.send([0])
    # If motors initialized
    if motors_p != 0:
        if motors_p.is_alive():
            motors_p.terminate()
            print("Motors terminated")
        motors_p.close()
    # If motors connection initialized
    if motors_conn != 0:
        motors_conn.close()
    exit()


def predict_defence_position():
    global robot_x_target, robot_y_target
    robot_x_target = 90.0
    print("puck_speed_x: {}".format(puck_speed_x))
    print("robot_y: {}".format(robot_y))
    # If puck is moving away from robot
    if puck_speed_x <= 0:
        print("Puck moving away from robot")
        robot_y_target = 24.0
    # If puck is coming towards robot
    else:
        print("Puck moving towards robot")
        slope = abs(puck_speed_y / puck_speed_x)
        print("slope: {}".format(slope))
        dist = robot_x - puck_x
        print("dist: {}".format(dist))
        additional_y = slope * dist
        print("additional y: {}".format(additional_y))
        #If puck is behind robot
        if dist < 0 or slope > 2:
            print("Puck behind net or slope too large")
            robot_y_target = 24.0
        # If puck is moving down table vertically
        elif puck_speed_y > 0:
            print("moving down table")
            projected_y = puck_y + additional_y
            # No wall bounces
            if projected_y < TABLE_HEIGHT:
                print("No wall bounces")
                robot_y_target = projected_y
            # Wall bounces
            else:
                print("Wall bounces")
                dist_past = projected_y - TABLE_HEIGHT
                num_bounces = dist_past // TABLE_HEIGHT + 1
                remainder = dist_past % TABLE_HEIGHT
                # Coming off top wall
                if num_bounces % 2 == 0:
                    robot_y_target = remainder
                # Coming off bottom wall
                else:
                    robot_y_target = TABLE_HEIGHT - remainder
        # Puck is moving up table vertically
        else:
            print("moving up table")
            projected_y = puck_y - additional_y
            # No wall bounces
            if projected_y > 0:
                print("No wall bounces")
                robot_y_target = projected_y
            # Wall bounces
            else:
                print("Wall bounces")
                dist_past = -1 * projected_y
                num_bounces = dist_past // TABLE_HEIGHT + 1
                remainder = dist_past % TABLE_HEIGHT
                # Coming off top wall
                if num_bounces % 2 == 1:
                    robot_y_target = remainder
                # Coming off bottom wall
                else:
                    robot_y_target = TABLE_HEIGHT - remainder

def calculate_targ_distances():
    global x_targ_dist, y_targ_dist
    x_targ_dist = robot_x_target - robot_x
    y_targ_dist = robot_y_target - robot_y


def follow_puck_vertical():
    global x_targ_dist, y_targ_dist
    x_targ_dist = 0
    y_targ_dist = puck_y - robot_y


def strategy(conn):
    global vision_conn
    global puck_x, puck_y, puck_x_last, puck_y_last
    vision_conn = conn

    print("Initializing motors.")
    initialize_motors_process()
    print("Motors initialized.")

    # Inform vision that process initialized successfully
    vision_conn.send([1, True])

    while(True):
        msg = vision_conn.recv()
        # If terminate request
        if msg[0] == 0:
            terminate_strategy()
        update_locations(msg)
        update_puck_speed()
        #follow_puck_vertical()
        predict_defence_position()
        calculate_targ_distances()
        motors_conn.send([4, x_targ_dist, y_targ_dist])

