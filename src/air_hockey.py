'''
GUI for Air Hockey Game 
'''

import time 
import os
import RPi.GPIO as GPIO
import sys
import pygame
from pygame.locals import *
from multiprocessing import Process, Pipe
from vision import vision

# Connection Globals
vision_conn = 0
vision_p = 0
motor_conn = 0
motor_p = 0

# Env variables for TFT
#os.putenv('SDL_VIDEODRIVER','fbcon')
#os.putenv('SDL_FBDEV','/dev/fb1')
#os.putenv('SDL_MOUSEDRV','TSLIB')
#os.putenv('SDL_MOUSEDEV','/dev/input/touchscreen')

pygame.init()

# Pygame parameters
size=width,height=320,240
screen=pygame.display.set_mode(size)
BLACK=0,0,0
WHITE=255,255,255

# Game Globals
code_run = True
game_on = False

# Frame rate
fps=30
clk=pygame.time.Clock()

# Bailout button
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Callback for bailout button
def gpio27_callback(channel):
    terminate_air_hockey()

# Set up callback on button press
GPIO.add_event_detect(27, GPIO.FALLING, callback=gpio27_callback, bouncetime=400)


# Font object and text objects w/ Rects
font = pygame.font.SysFont(None, 20)
padding = 30

exit_text = font.render('EXIT', True, WHITE)
exit_text_rect = exit_text.get_rect(topright=(width-padding, height-50))

start_text = font.render('START GAME', True, WHITE)
start_text_rect = start_text.get_rect(topleft=(padding, height-50))

human_text = font.render('HUMAN', True, WHITE)
human_text_rect = human_text.get_rect(center=(50, 50))

robot_text = font.render('ROBOT', True, WHITE)
robot_text_rect = robot_text.get_rect(center=(270, 50))

human_score = font.render('0', True, WHITE)
human_score_rect = human_score.get_rect(center=(50, 100))

robot_score = font.render('0', True, WHITE)
robot_score_rect = robot_score.get_rect(center=(270, 100))

# Background images and Rects
bg_image=pygame.image.load("air_hockey.jpg")
bg_image_rs=pygame.transform.scale(bg_image,(200,200))
bg_image_rect=bg_image_rs.get_rect(center=(width/2,(height/2)-50))


def terminate_air_hockey():
    print("Air Hockey terminating.")
    # Terminate vison process
    vision_conn.send([0])
    # If vision is initialized
    if vision_p != 0:
        if vision_p.is_alive():
            vision_p.terminate()
    # If vision connection initialized
    if vision_conn != 0:
        vision_conn.close()
    GPIO.cleanup()

    pygame.display.quit()
    pygame.quit()

    print("Thanks for playing Air Hockey!")
    exit()


def initialize_vision_process():
    global vision_conn, vision_p
    vision_conn, child_conn = Pipe()
    vision_p = Process(target=vision, args=(child_conn,))
    vision_p.start()
    # Wait for vision process to initalize
    vision_init = vision_conn.recv()
    if not (vision_init[0] == 1 and vision_init[1]):
        terminate_air_hockey()


def air_hockey():
    global code_run, game_on
    
    # Initialize Vision Process
    print("Initializing vision")
    initialize_vision_process()
    print("Vision initialized")

    while code_run:    
        clk.tick(fps)
        screen.fill(BLACK)
        # Search for taps in event list
        for event in pygame.event.get():
            if event.type==pygame.MOUSEBUTTONUP:
                # Save position
                pos = pygame.mouse.get_pos()
                # Home menu
                if not game_on:
                    # Tap quit button
                    if exit_text_rect.collidepoint(pos):
                        code_run = False
                    # Hit start button
                    elif start_text_rect.collidepoint(pos):
                        game_on = True
                        vision_conn.send([2, True])
                else:
                    if exit_text_rect.collidepoint(pos):
                        game_on = False
                        vision_conn.send([2, False])
                        print("Air Hockey -> Vision Pause")

        # Draw Screen
        if game_on:
            screen.blit(exit_text, exit_text_rect)
            screen.blit(human_text, human_text_rect)
            screen.blit(robot_text, robot_text_rect)
            screen.blit(human_score, human_score_rect)
            screen.blit(robot_score, robot_score_rect)
        else:
            screen.blit(bg_image_rs, bg_image_rect)
            screen.blit(exit_text, exit_text_rect)
            screen.blit(start_text, start_text_rect)
    
        pygame.display.flip()
    
    terminate_air_hockey()


if __name__ == '__main__':
    air_hockey()
