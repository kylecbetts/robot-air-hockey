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
puck_y_last = 49.0
puck_speed_x = 0
puck_speed_y = 0
puck_speed = 0
puck_direction = 0

# Robot Globals
defence_position = 0
robot_x = 0
robot_y = 0
robot_x_desired = 0
robot_y_desired = 0
robot_collision_time = 0

# Motor Constants
motors_command = "STOP"


def update_puck_speed():
    global puck_x, puck_y, puck_x_last, puck_y_last, puck_direction
    global puck_speed_x, puck_speed_y, puck_speed
    delta_x = puck_x - puck_x_last
    delta_y = puck_y - puck_y_last
    puck_speed_x = delta_x * 30
    puck_speed_y = delta_y * 30
    puck_direction = math.atan(delta_x/delta_y)
    puck_speed = math.hypot(puck_speed_x, puck_speed_y)
    

def update_locations(msg):
    global puck_x, puck_y, puck_x_last, puck_y_last
    global robot_x, robot_y
    # If puck was found
    if msg[1] != -1:
        puck_x_last = puck_x
        puck_y_last = puck_y
        puck_x = msg[1]
        puck_y = msg[2]
    else:
        puck_x_last = puck_x
        puck_x = puck_x + puck_speed_x
        puck_y_last = puck_y
        puck_y = puck_y + puck_speed_y
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
        motors_p.close()
    # If motors connection initialized
    if motors_conn != 0:
        motors_conn.close()
    exit()


def follow_puck_vertical():
    global motors_command
    if puck_y < robot_y:
        if robot_y < TABLE_PADDING:
            motors_command = "STOP"
        else:
            motors_command = "RIGHT"
    elif puck_y > robot_y:
        if robot_y > TABLE_WIDTH - TABLE_PADDING:
            motors_command = "STOP"
        else:
            motors_command = "LEFT"
    else:
        motors_command = "STOP"


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
        follow_puck_vertical()
        motors_conn.send([4, motors_command])

