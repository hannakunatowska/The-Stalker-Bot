import ai_detection
from main import stop, move_backwards, move_forward, turn, follow


def avoid_obstacle():

    angle, direction, obstacle, person_height = ai_detection.get_tracking_data() # Gets necessary data from the AI camera

    """
    Avoids an obstacle by stopping.

    Arguments:
        None

    Returns:
        None
    
    """

    print("\nStopping...")
    stop()
    move_backwards(time)


    # stop

    # if person
    #   if centered

    #       check left

    #       if not obstacle 
    #           go_around_left()

    #       else
    #           check right 

    #           if not obstacle
    #               go around right 

    #               continue
    
    print("\nStopping...")
    stop()

    if person_height is not None:
         if direction == "centered":
              
              print("\nChecking left...")
              check_left

              if not obstacle:
                   print("\nObstacle not detected, going around...")
                   go_around_left()

              else:
                   print("\nNo person detected, checking right...")
                   check_right

                   if not obstacle:
                        print("\nNo obstacle detected, going around...")
                        go_around_right()
              
                   
              

    # if not person

    #   check left 

    #   if person and not obstacle
    #       follow

    #   elif not person and not obstacle 
    #       go_around_left()

    #   else 
    #       check right 

    #       if person and not obstacle
    #           follow

    #       elif not person and not obstacle 
    #           go_around_right()

    #       else 
    #           stop 

    if person_height is None:
            print("\nNo person detected, checking left...")

            check_left()

            if ((person_height is not None) and (not obstacle)):
                 print("\nPerson found, following...")
                 follow()
            
            elif ((person_height is None) and (not obstacle)):
                 print("\nNo person detected, no obstacle detected, going around...")
                 go_around_left

            else:
                 print("\nNo person to the left, checking right...")
                 check_right

                 if ((person_height is not None) and (not obstacle)):
                      print("\nPerson found, following...")
                      follow()

                 elif ((person_height is None) and (not obstacle)):
                      print("\nNo person detected, no obstacle detected, going around...")
                      go_around_right

                 else:
                      print("\nNo persen detected, stopping...")
                      stop()


            


def go_around_left():
    move_forward()
    turn("left", 180) 
    turn("right",0) 

def go_around_right():
    move_forward()
    turn("right",0) 
    turn("left", 180) 
    
def check_left():

def check_right():

    

