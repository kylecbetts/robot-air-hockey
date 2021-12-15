import cv2 as cv
import numpy as np
import os
import math
from multiprocessing import Process, Pipe
from strategy import strategy

# Connection Globals
air_hockey_conn = 0
strategy_conn = 0
strategy_p = 0

# OpenCV Constants
FONT = cv.FONT_HERSHEY_SIMPLEX

# Camera Constants
CAM_WIDTH = 640
CAM_HEIGHT = 480
CAM_FPS = 30

# Video Globals
frame = np.zeros((CAM_WIDTH, CAM_HEIGHT, 3), np.uint8)
lower_object_hue = 15
upper_object_hue = 30
upper_table_gray = 40

# Puck Globals
puck_x = 0
puck_y = 0
puck_r = 0
puck_x_cord = 0
puck_y_cord = 0
puck_max_area = 1500
puck_min_area = 500
puck_located = False

# Robot Globals
robot_x= 0
robot_y = 0
robot_r = 0
robot_x_cord = 0
robot_y_cord = 0
robot_max_area = 500
robot_min_area = 50
robot_located = False

# Table Globals
table_top_left = [25, 68]
table_top_right = [636, 60]
table_bottom_left = [30, 370]
table_bottom_right = [640, 362]
table_middle_top = ((table_top_left[0] + table_top_right[0]) / 2, (table_top_left[1] + table_top_right[1]) / 2)
table_middle_bottom = ((table_bottom_left[0] + table_bottom_right[0]) / 2, (table_bottom_left[1] + table_bottom_right[1]) / 2)
table_min_area = 100000
table_max_area = 190000
table_located = False

# Conversion Globals
TABLE_HEIGHT = 48.0
TABLE_WIDTH = 98.0
TABLE_PADDING = 5.0
pix_to_cordinates_x_scalar = TABLE_WIDTH / (table_top_right[0] - table_top_left[0])
pix_to_cordinates_y_scalar = TABLE_HEIGHT / (table_bottom_right[1] - table_top_right[1])

# Game Globals
game_on = False


def initialize_camera(cap):
    global CAM_WIDTH, CAM_HEIGHT, CAM_FPS
    CAM_WIDTH = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    CAM_HEIGHT = cap.get(cv.CAP_PROP_FRAME_WIDTH)
    CAM_FPS = cap.get(cv.CAP_PROP_FPS)


def calibrate_table():
    global frame, table_located, table_top_left, table_top_right, table_bottom_right, table_bottom_left, table_middle_top, table_middle_bottom
    global pix_to_cordinates_x_scalar, pix_to_cordinates_y_scalar
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    ret, gray = cv.threshold(gray, upper_table_gray, 255, cv.THRESH_BINARY)
    gray = cv.GaussianBlur(gray, (3,3), 0)
    _, contours, _ = cv.findContours(gray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    if not (contours is None): 
        for cnt in contours:
            area = cv.contourArea(cnt)
            cv.drawContours(frame, [cnt], 0, (255,0,0), 3)
            rect = cv.minAreaRect(cnt)
            box = cv.boxPoints(rect)
            box = np.int0(box)
            cv.drawContours(frame, [box], 0, (0,255,0), 3)
            # Check if table
            if area < table_max_area and area > table_min_area:
                rect = cv.minAreaRect(cnt)
                box = cv.boxPoints(rect)
                box = np.int0(box)
                table_bottom_left = box[0]
                table_top_left = box[1]
                table_top_right = box[2]
                table_bottom_right = box[3]
                table_middle_top = ((table_top_left[0] + table_top_right[0]) / 2, (table_top_left[1] + table_top_right[1]) / 2)
                table_middle_bottom = ((table_bottom_left[0] + table_bottom_right[0]) / 2, (table_bottom_left[1] + table_bottom_right[1]) / 2)
                pix_to_cordinates_x_scalar = TABLE_WIDTH / (table_top_right[0] - table_top_left[0])
                pix_to_cordinates_y_scalar = TABLE_HEIGHT / (table_bottom_right[1] - table_top_right[1])
                table_located = True
                break


def draw_table():
    # Draw table outline
    pts = np.array([table_top_left, table_top_right, table_bottom_right, table_bottom_left], np.int32)
    pts = pts.reshape((-1,1,2))
    cv.polylines(frame, [pts], True, (255,0,0), 4)

    # Draw table center line
    #cv.line(frame, table_middle_top, table_middle_bottom, (0,0,255), 4)

def initialize_strategy_process():
    global strategy_conn, stategy_p
    strategy_conn, child_conn = Pipe()
    strategy_p = Process(target=strategy, args=(child_conn,))
    strategy_p.start()
    # Wait for strategy process to initalize
    strategy_init = strategy_conn.recv()
    if not (strategy_init[0] == 1 and strategy_init[1]):
        print("Failed to initalize strategy.")
        terminate_vision()


def terminate_vision():
    print("Vision terminating.")
    # Terminate strategy process
    strategy_conn.send([0])
    # If strategy initialized
    if strategy_p != 0:
        if strategy_p.is_alive():
            strategy_p.terminate()
        strategy_p.close()
    # If strategy connection initialized
    if strategy_conn != 0:
        strategy_conn.close()
    exit()
        


def pixels_to_table_cordinates(pix_x, pix_y):
    cord_y = 0
    # If on players side
    if pix_x < table_middle_top[0]:
        cord_y = (pix_y - table_top_left[1]) * pix_to_cordinates_y_scalar
    # If on robot side
    else:
        cord_y = (pix_y - table_top_right[1]) * pix_to_cordinates_y_scalar

    cord_x = 0
    if cord_y < TABLE_HEIGHT / 2:
        cord_x = (pix_x - table_top_left[0]) * pix_to_cordinates_x_scalar
    else: 
        cord_x = (pix_x - table_bottom_left[0]) * pix_to_cordinates_x_scalar

    # Safety Checks
    if cord_y < TABLE_PADDING:
        cord_y = TABLE_PADDING
    elif cord_y > TABLE_HEIGHT - TABLE_PADDING:
        cord_y = TABLE_HEIGHT - TABLE_PADDING
    if cord_x < TABLE_PADDING:
        cord_x = TABLE_PADDING
    elif cord_x > TABLE_WIDTH - TABLE_PADDING:
        cord_x = TABLE_WIDTH - TABLE_PADDING

    return (cord_x, cord_y)



def find_puck_and_robot():
    global  puck_located, robot_located, puck_x, puck_y, puck_r, robot_x, robot_y, robot_r
    global puck_x_cord, puck_y_cord, robot_x_cord, robot_y_cord
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    lower_color = np.array([lower_object_hue,100,100])
    upper_color = np.array([upper_object_hue,255,255])
    mask = cv.inRange(hsv, lower_color, upper_color)
    gray = cv.bitwise_and(gray, gray, mask=mask)
    gray = cv.GaussianBlur(gray, (5,5), 0)
    _, contours, _ = cv.findContours(gray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    puck_located = False
    robot_located = False
    if not (contours is None):
        for cnt in contours:
            area = cv.contourArea(cnt)
            # Check if puck
            if area < puck_max_area and area > puck_min_area:
                puck_located = True
                (x, y), r = cv.minEnclosingCircle(cnt)
                puck_x = int(x)
                puck_y = int(y)
                puck_r = int(r)
                puck_x_cord, puck_y_cord = pixels_to_table_cordinates(puck_x, puck_y)
            # Check if robot
            elif area < robot_max_area and area > robot_min_area:
                robot_located = True
                (x, y), r = cv.minEnclosingCircle(cnt)
                robot_x = int(x)
                robot_y = int(y)
                robot_r = int(r)
                robot_x_cord, robot_y_cord = pixels_to_table_cordinates(robot_x, robot_y)
    if not puck_located:
        puck_x_cord = -1
        puck_y_cord = -1
    if not robot_located:
        robot_y_cord = -1
        robot_y_cord = -1


def draw_puck_and_robot():
    if puck_located:
        cv.circle(frame, (puck_x, puck_y), puck_r, (0,0,255), 2)
    if robot_located:
        cv.circle(frame, (robot_x, robot_y), robot_r, (0,0,255), 2)


def vision(conn):
    global frame, air_hockey_conn, game_on
    air_hockey_conn = conn

    # Initialize Strategy Process
    print("Initializing strategy.")
    initialize_strategy_process()
    print("Strategy initialized.")

    # Initialize Video Capture
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera. Exiting...")
        terminate_vision()
    
    # Initialize Camera Globals
    initialize_camera(cap)

    i = 0
    # Calibrate Table 
    while (not table_located and i < 30):
        i += 1
        ret, frame = cap.read()
        calibrate_table()
        cv.imshow('frame', frame)
        if cv.waitKey(1) == ord('q'):
            break

    # Inform air hockey that process initialized successfully
    air_hockey_conn.send([1, True])

    while(True):
        # If not game, wait for message to start
        if not game_on:
            msg = air_hockey_conn.recv()
            if msg[0] == 2:
                if msg[1]:
                    game_on = True
            else:
                # Release the cap object
                cap.release()
                # Destroy all the windows
                cv.destroyAllWindows()
                terminate_vision()
        else:
            # Capture the video frame by frame
            ret, frame = cap.read()
            if not ret:
                print("Cannot receive frame. Exiting...")
                break
             
            # Find puck and robot then draw them
            find_puck_and_robot()
            draw_puck_and_robot()

            # Send puck and robot cordinates to strategy
            print("Cordinates: {} {} {}".format(puck_x_cord, puck_y_cord, robot_y_cord))
            strategy_conn.send([3, puck_x_cord, puck_y_cord, robot_x_cord, robot_y_cord])

            # Draw Table Lines
            draw_table()

            # Display the resulting frame
            cv.imshow('frame', frame)
            
            # Check for new messages
            if air_hockey_conn.poll():
                msg = air_hockey_conn.recv()
                if msg[0] == 2:
                    game_on = msg[1]
                else:
                    # Release the cap object
                    cap.release()
                    # Destroy all the windows
                    cv.destroyAllWindows()
                    terminate_vision()

            # Use Q key to exit
            if cv.waitKey(1)  == ord('q'):
                break


if __name__ == '__main__':
    vision(0)
