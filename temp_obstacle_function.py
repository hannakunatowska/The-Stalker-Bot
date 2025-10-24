import ai_detection
import time
from main import stop, move_backwards, move_forward, turn, follow

def avoid_obstacle():

     obstacle_note_front = False
     obstacle_note_side = False
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

               #-------------- checking left ----------------

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

               # checking left

               #-------------- checking right ----------------

               else: # no person to the left
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
                              
               # -------------------------------------------

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

def check_right():

    

