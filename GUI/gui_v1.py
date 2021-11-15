'''
GUI v1 

Initial functionality with basic buttons. 

Basic background and limited use 

Next Iteration - Increased functionality with polished look
'''

import time 
import os
#import RPi.GPIO as GPIO
import sys
import pygame
from pygame.locals import *

# Env variables for TFT
#os.putenv('SDL_VIDEODRIVER','fbcon')
#os.putenv('SDL_FBDEV','/dev/fb1')
#os.putenv('SDL_MOUSEDRV','TSLIB')
#os.putenv('SDL_MOUSEDEV','/dev/input/touchscreen')

pygame.init()
pygame.mouse.set_visible(True)

# Pygame parameters
size=width,height=320,240
speed1=[1,1]
speed2=[1,1]
screen=pygame.display.set_mode(size)
BLACK=0,0,0
WHITE=255,255,255

# Frame rate and Clock object to enforce it
fps=160
clk=pygame.time.Clock()

# Used for button placement
padding=30

# Enable timeout functionality
start_time=time.time()
timeout=300

# Enable pin 27 for bailout button
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Callback for bailout button
#def gpio27_callback(channel):
 #   global code_run
 #  print("Quit")
 #  code_run=False

# Set up callback on button press
#GPIO.add_event_detect(27, GPIO.FALLING, callback=gpio27_callback, bouncetime=400)

# Font object and text objects w/ Rects
font = pygame.font.SysFont(None, 20)
exit_text = font.render('EXIT GAME', True, WHITE)
exit_text_rect = exit_text.get_rect(topright=(width-padding, height-50))

start_text = font.render('START GAME', True, WHITE)
start_text_rect = start_text.get_rect(topleft=(padding, height-50))

back_text = font.render('BACK', True, WHITE)
back_text_rect = back_text.get_rect(topright=(width-padding, height-50))

back_text_doctor = font.render('Back', True, WHITE)
back_text_rect_doctor = back_text_doctor.get_rect(center=((width*3)/5, height-50))

back_text_patient = font.render('Back', True, WHITE)
back_text_rect_patient = back_text_patient.get_rect(center=((width*4)/5, 220))

back_text_log = font.render('Back', True, WHITE)
back_text_rect_log = back_text_log.get_rect(center=((width*4)/5, 220))

player1_text = font.render('Player 1', True, WHITE)
player1_text_rect = player1_text.get_rect(center=(50, 50))

player2_text = font.render('Player 2', True, WHITE)
player2_text_rect = player2_text.get_rect(center=(270, 50))


# Ball images and Rects
bg_image=pygame.image.load("bg_image_resized.jpg")
bg_image_rs=pygame.transform.scale(bg_image,(200,200))
bg_iamge_rect=bg_image_rs.get_rect(center=(width/2,(height/2)-50))


code_run=True # When False, loop breaks - quit button
game_run=False # Only move balls when True - start button

while code_run and time.time()-start_time<timeout:    
    # Enforce frame rate
    clk.tick(fps)
    # Clear Screen
    screen.fill(BLACK)
    # Search for taps in event list
    for event in pygame.event.get():
        if event.type==pygame.MOUSEBUTTONUP:
            print(pygame.mouse.get_pos())
            # Save position
            pos = pygame.mouse.get_pos()
            # Home menu
            if not game_run:
                # Tap quit button
                if exit_text_rect.collidepoint(pos):
                    code_run = False
                # Hit start button
                elif start_text_rect.collidepoint(pos):
                    game_run = True
            
    
    
    # Home menu
    if game_run:
        screen.blit(back_text, back_text_rect)
        screen.blit(player1_text, player1_text_rect)
        screen.blit(player2_text, player2_text_rect)
        if back_text_rect.collidepoint(pos):
            game_run=False    
        # Blit the buttons
        # Home menu
    else:
        # Blit the balls
        #screen.blit(ball1, ballrect1)
        #screen.blit(ball2, ballrect2)
        # Blit the buttons
        screen.blit(bg_image_rs, bg_iamge_rect)
        screen.blit(exit_text, exit_text_rect)
        screen.blit(start_text, start_text_rect)
    
    # Always display the coordinate string
    #screen.blit(cord_text, cord_text_rect)

    pygame.display.flip()
    

# Clean up when program exit
#GPIO.cleanup()
