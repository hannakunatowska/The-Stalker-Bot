# --- Imports ---

import ai_detection
import time
from gpiozero import Servo # Imports the Servo class from the gpiozero module for controlling servo motors
from main import stop, move_backwards, move_forward, turn, follow

# --- Servo definitions ---

servo_maximum_position = 1 # looking right
servo_minimum_position = -1 # looking left
servo_minimum_pulse_width = 0.5 / 1000
servo_maximum_pulse_width = 2.5 / 1000
servo_step = 0.04
servo_threshold = 0.2
servo_change_threshold = 0.005
servo_smooth_speed = 0.005
servo_step_delay = 0.005

# --- Servo setup ---

servo = Servo(18, min_pulse_width = servo_minimum_pulse_width, max_pulse_width = servo_maximum_pulse_width) # Creates a servo object on GPIO pin 18 with specified pulse widths
servo_position = 0.0 # Creates a variable for the servo position and initializes its value to 0.0 (center position)
servo.value = servo_position # Sets the position to "servo_position"

def avoid_obstacle():

     """
     Avoids an obstacle by stopping.

     Arguments:
          None

     Returns:
         None
    
     """

     # --- Temporary variables ---

     obstacle_note_front = False
     obstacle_note_side = False
     timer = 0
     angle, direction, obstacle, person_height = ai_detection.get_tracking_data() # Gets necessary data from the AI camera


     print("\nStopping...")
     stop() # stop

     print("\nMoving backwards...")
     
     timer = time.time() # Start the timer
     while time.time() - timer < 1: # Move backwards for 1 seconds
          move_backwards()
     

     if person_height is not None: # if person
          if direction == "centered": # if centered
              
               print("\nChecking left...")
               check_left() # check left

               if not obstacle: # if not obstacle 
                    print("\nObstacle not detected, going around...")
                    go_around_left() # go_around_left()

                    print("\nNow following...")
                    follow() # following after going around

                    return

               else: # else obstacle   
                    print("\nNo person detected, checking right...")
                    check_right() # check right 

                    if not obstacle: # if not obstacle
                         print("\nNo obstacle detected, going around...")
                         go_around_right() # go around right 

                         print("\nNow following...")
                         follow() # following after going around

                         return



     if person_height is None: # if no person

          if direction == "centered":
               print("\nNotes if there is an obstacle or not")
               obstacle_note_front = obstacle

               # --- Checking Left ---

               print("\nNo person detected, checking left...")
               check_left() # check left

               if person_height is not None: # checks if theres a person the left

                    print("\nNoting if there's an obstacle to the right")
                    check_right() # checking right

                    obstacle_note_side = obstacle

                    check_left()

                    if not obstacle: # if no obstacle to the left
                         print("\nPerson found, following...")
                         follow() # follow

                         return
                    
                    elif obstacle: # elif person and obstacle to the left

                         """
                         
                         backing to right so that the person is straight ahead

                         now facing the past left

                         """

                         if obstacle_note_front: # if there's an obstacle to the right
                              print("\nObstacle on the right, checking left...")
                              check_left() # check left for obstacle again

                              if not obstacle: # if no obstacle
                                   print("\nPerson and obstacle detected, going around...")
                                   go_around_left() # go around left

                                   print("\nNow following...")
                                   follow() # following after going around

                                   return

                              elif obstacle_note_side: # sorrounded by obstacles
                                   print("\nSorrounded by obstacles, stopping...")
                                   stop() # stopping

                                   return
                              
                              else: # else no obstacle behind

                                   """
                                   
                                   backing out
                                   
                                   """

                         else: # else there is no obstacle to the right
                              print("\nNo obstacle to the right, going around...")
                              go_around_right() # going around right

                              print("\nNow following...")
                              follow() # following after going around

                              return

               # Checking Left

               # --- Checking Right ---

               else: # else no person to the left
                    print("\nNo person to the left, checking right...")
                    check_right() # check right
               
                    if person_height is not None: # person to the right 

                         print("\nNoting if there's an obstacle to the left...")
                         check_left() # check left

                         obstacle_note_side = obstacle

                         check_right()

                         if not obstacle: # if no obstacle
                              print("\nPerson found, following...")
                              follow() # follow

                              return

                         elif obstacle: # elif obstacle

                              """
                         
                              backing to left so that the person is straight ahead

                              now facing the past right

                              """

                              if obstacle_note_front: # if there's an obstacle to the left
                                   print("\nObstacle to the left, checking right again...")
                                   check_right() # checking right again

                                   if not obstacle: # if no obstacle on right side
                                        print("\nNo obstacle to the right, going around...")
                                        go_around_right # going around right
                                        
                                        print("\nNow following...")
                                        follow() # following

                                        return
                                   
                                   elif obstacle_note_side: # else sorrounded by obstacles
                                        print("\nSorrounded by obstacles, stopping...")
                                        stop() #stopping

                                        return
                                   
                                   else: # else no obstacle behind

                                        """
                                        
                                        backing out
                                        
                                        """

                              else: # else no obstacle on left side
                                   print("\nNo obstacle to the left, going around...")
                                   go_around_left() # going around left

                                   print("\nNow following...")
                                   follow() # following

                                   return
                              
               # Checking Right
               
               # --- No Person Found ---

                    else: # else no person detected
                         print("\nNo persen detected, stopping...")
                         stop() # stopping


            


def go_around_left():

     """

     turn left until obstacle is not detected

     possibly holding the obstacle to 45 or 90 degrees of car

     """

     move_forward()
     turn("left", 180) 
     turn("right",0) 

def go_around_right():

     """

     turn right until obstacle is not detected

     """

     move_forward()
     turn("right",0) 
     turn("left", 180) 
    
def check_left():

     """
     
     Turning the servo left
     
     """

     servo.value = servo_minimum_position

def check_right():

     """
     
     Turning the servo right
     
     """

     servo.value = servo_maximum_position

    

