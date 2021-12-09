import cv2 as cv
import numpy as np
import os

#os.putenv('SDL_VIDEODRIVER', 'fbcon')
#os.putenv('SDL_FBDEV', '/dev/fb1')
#os.putenv('SDL_MOUSEDRV', 'TSLIB')
#os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# OpenCV Constants
FONT = cv.FONT_HERSHEY_SIMPLEX

# Camera Constants
CAM_WIDTH = 640
CAM_HEIGHT = 480
CAM_FPS = 30

# Video Globals
frame = np.zeros((CAM_WIDTH, CAM_HEIGHT, 3), np.uint8)

# Puck Globals
puck_x = 0
puck_y = 0
puck_r = 0
puck_old_x = 0
puck_old_y = 0
puck_speed_x = 0
puck_speed_y = 0
puck_speed = 0
puck_direction = 0
puck_max_area = 1400
puck_min_area = 800
puck_located = False

# Robot Globals
robot_x= 0
robot_y = 0
robot_r = 0
robot_impact_x = 0
robot_impact_y = 0
robot_impact_time = 0
robot_max_area = 800
robot_min_area = 100
robot_located = False

# Table Globals
table_top_left = [0, 0]
table_top_right = [CAM_WIDTH, 0]
table_bottom_left = [0, CAM_HEIGHT]
table_bottom_right = [CAM_WIDTH, CAM_HEIGHT]
table_middle_top = (CAM_WIDTH/2, 0)
table_middle_bottom = (CAM_WIDTH/2, CAM_HEIGHT)


def initialize_camera(cap):
    global CAM_WIDTH, CAM_HEIGHT, CAM_FPS
    CAM_WIDTH = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    CAM_HEIGHT = cap.get(cv.CAP_PROP_FRAME_WIDTH)
    CAM_FPS = cap.get(cv.CAP_PROP_FPS)


def calibrate_table():
    pass


def draw_table():
    # Draw table outline
    pts = np.array([table_top_left, table_top_right, table_bottom_right, table_bottom_left], np.int32)
    pts = pts.reshape((-1,1,2))
    cv.polylines(frame, [pts], True, (255,0,0), 4)

    # Draw table center line
    cv.line(frame, table_middle_top, table_middle_bottom, (0,0,255), 4)


def find_puck_and_robot():
    global puck_located, robot_located, puck_x, puck_y, puck_r, robot_x, robot_y, robot_r
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    lower_yellow = np.array([20,100,100])
    upper_yellow = np.array([30,255,255])
    mask = cv.inRange(hsv, lower_yellow, upper_yellow)
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
            # Check if robot
            elif area < robot_max_area and area > robot_min_area:
                robot_located = True
                (x, y), r = cv.minEnclosingCircle(cnt)
                robot_x = int(x)
                robot_y = int(y)
                robot_r = int(r)


def draw_puck_and_robot():
    if puck_located:
        cv.circle(frame, (puck_x, puck_y), puck_r, (0,255,0), 2)
    if robot_located:
        cv.circle(frame, (robot_x, robot_y), robot_r, (255,0,0), 2)


def play_game():
    global frame
    # Initialize Video Capture
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera. Exiting...")
        exit()
    
    # Initialize Camera Globals
    initialize_camera(cap)

    # Game Loop
    while(True): 
        # Capture the video frame by frame
        ret, frame = cap.read()
        if not ret:
            print("Cannot receive frame. Exiting...")
            break

        # Find puck and robot then draw them
        find_puck_and_robot()
        draw_puck_and_robot()

        # Draw Table Lines
        draw_table()

        # Display the resulting frame
        cv.imshow('frame', frame)

        # Use Q key to exit
        if cv.waitKey(1)  == ord('q'):
            break
  
    # Release the cap object
    cap.release()
    # Destroy all the windows
    cv.destroyAllWindows()


play_game()
