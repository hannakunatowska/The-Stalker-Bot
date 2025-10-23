import ai_detection
import time
from main import stop, move_backwards, move_forward, turn, follow

def avoid_obstacle():

     obstacle_note = False
     timer = 0
     angle, direction, obstacle, person_height = ai_detection.get_tracking_data() # Gets necessary data from the AI camera

     """
     Avoids an obstacle by stopping.

     Arguments:
          None

     Returns:
         None
    
     """
    
     print("\nStopping...")
     stop()    # stop

     print("\nMoving backwards...")
     
     timer = time.time()  # Start the timer
     while time.time() - timer < 1:  # Move backwards for 1 seconds
          move_backwards()
     

     if person_height is not None: # if person
          if direction == "centered":   # if centered
              
               print("\nChecking left...")
               check_left()   # check left

               if not obstacle:    # if not obstacle 
                    print("\nObstacle not detected, going around...")
                    go_around_left()    # go_around_left()

               else:     # else obstacle   
                    print("\nNo person detected, checking right...")
                    check_right()  # check right 

                    if not obstacle:    # if not obstacle
                         print("\nNo obstacle detected, going around...")
                         go_around_right()   # go around right 



     if person_height is None:     # if no person
          if direction == "centered":
               print("\nNotes if there is an obstacle or not")
               obstacle_note = obstacle

               print("\nNo person detected, checking left...")
               check_left()   # check left

               if ((person_height is not None) and (not obstacle)):   # if person and not obstacle
                    print("\nPerson found, following...")
                    follow()     # follow
                    return
               
               elif ((person_height is not None) and (obstacle)):     # elif person and obstacle

                    if obstacle_note:   # if theres an obstacle to the right

                         check_left()

                         print("\nPerson and obstacle detected, going around...")
                         go_around_left()  # go around left

                    if ((person_height is not None) and (not obstacle)):   # if person and not obstacle
                         print("\nPerson found, following...")
                         follow()     # follow
                         return

               print("\nNo person to the left, checking right...")
               check_right()  # check right

               if ((person_height is not None) and (not obstacle)):  # if person and not obstacle
                    print("\nPerson found, following...")
                    follow()     # follow

               elif ((person_height is None) and (not obstacle)):    # elif no person and not obstacle
                    print("\nNo person detected, no obstacle detected, going around...")
                    go_around_right() # go around right

                    print("\nChecking right...")
                    check_right()  # check right

                    if ((person_height is not None) and (not obstacle)):  # if person and not obstacle
                         print("\nPerson found, following...")
                         follow()     # follow

               else:     # else no person detected
                    print("\nNo persen detected, stopping...")
                    stop()   # stop


            


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

def check_right():

    

