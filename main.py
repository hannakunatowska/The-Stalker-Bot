
# --- Imports ---

import time
import ai_detection
from remote_controller import press, unpress, check_button_press, move_backwards_button_pin, move_forward_button_pin, turn_left_button_pin, turn_right_button_pin
from ultrasonic_sensor import get_distance

# --- Definitions ---

turn_time_per_degree = 0.9 / 90
target_minimum_height = 0.8
target_maximum_height = 0.95
safe_distance_in_cm = 40
max_angle_offset = 10
follow_loop_update_time = 0.1

first_timer = 0
first_timer_off = True
first_wait_time = 1

second_timer = 0
second_timer_off = True
second_wait_time = 0.01
log_file_path = "robot_log.txt"

# Log initialization

with open(log_file_path, "w") as f:
    f.write("Robot session started")

# --- Helper functions ---

def print_and_log(message):

    """
    Prints a message and writes it to a log file.

    Arguments:
        "message":

    Returns:
        None
    
    """

    print("\n" + message)

    with open(log_file_path, "a") as f:
        f.write("\n" + message)
        
def move_forward():

    """
    Moves the car forward.

    Arguments:
        "press_duration": The duration of the simulated button press.

    Returns:
        None

    """

    unpress(move_backwards_button_pin)
    press(move_forward_button_pin)

def move_backwards():

    """
    Moves the car backwards.

    Arguments:
        "press_duration": The duration of the simulated button press (default set to 0.3 s).

    Returns:
        None
        
    """
    
    unpress(move_forward_button_pin)
    press(move_backwards_button_pin)

def stop():

    """
    Stops the car.

    Arguments:
        None
    
    Returns:
        None

    """

    unpress(move_forward_button_pin)
    unpress(move_backwards_button_pin)

def turn(direction, angle):

    """
    Turns the car.

    Arguments:
        "direction": The turning direction.
        "angle": The angle to the person.

    Returns:
        None
    
    """

    if time.time() - first_timer > first_wait_time:

        if direction == "right" and not check_button_press(turn_right_button_pin):
            unpress(turn_left_button_pin)
            time.sleep(0.01)
            press(turn_right_button_pin)

        if direction == "left" and not check_button_press(turn_left_button_pin):
            unpress(turn_right_button_pin)
            time.sleep(0.01)
            press(turn_left_button_pin)

    if time.time() - second_timer > second_wait_time:
        if direction == "middle":
            unpress(turn_right_button_pin)
            unpress(turn_left_button_pin)

    print_and_log(f"Turned {direction} (angle was {angle:.1f})")

def avoid_obstacle():

    """
    Avoids an obstacle by stopping.

    Arguments:
        None

    Returns:
        None
    
    """

    print_and_log("Stopping...")
    stop()

# --- Main program loop ---

def follow():

    global first_timer, second_timer, first_timer_off, second_timer_off

    """
    Runs the person-following loop.

    Arguments:
        None

    Returns:
        None
    
    """

    while True:

        angle, direction, obstacle, person_height = ai_detection.get_tracking_data() # Gets necessary data from the AI camera

        distance_in_cm = get_distance() # Gets distance to closest obstacle from ultrasonic sensor
        
        if (not (person_height < target_minimum_height)): # person is too close or does not exist

            # resets the first timer if second timer is on and its within the given time
            if ((time.time() - first_timer < first_wait_time) and (not second_timer_off)): 
                first_timer_off = True
            
            

        if obstacle or distance_in_cm <= safe_distance_in_cm: # If either the AI camera or the ultrasonic sensor detects an obstacle:
            print_and_log("Trying to avoid obstacle...")
            turn("middle", angle)
            avoid_obstacle()
            continue
            
        if person_height is None:
            print_and_log("No person detected, waiting...")
            turn("middle", angle)
            stop()
            continue

        print_and_log(f"Normalized person height (Person height / Total frame height) = {person_height:.2f}")

        if person_height < target_minimum_height:
            

             # resets the second timer if first timer is on and its within the given time
            if ((time.time() - second_timer < second_wait_time) and (not first_timer_off)): 
                second_timer_off = True

            # turns the first timer on
            if first_timer_off:
                first_timer = time.time()
                first_timer_off = False
                second_timer_off = True

            # turns the second timer on
            if second_timer_off:
                second_timer = time.time()
                second_timer_off = False
                first_timer_off = True

            

            print("\nPerson is too far away, trying to move forward...")
            move_forward()            
            print_and_log("Person is too far away, trying to move forward...")

            move_forward()

            if direction == "centered":

                if abs(angle - 90) > max_angle_offset:

                    if angle < 90:
                        turn("right", angle)
                    
                    else:
                        turn("left", angle)
                    
                    continue
                
                else:
                    turn("middle", angle)
            
            elif direction in ("limit reached (left)", "limit reached (right)"):

                if angle < 90:
                    turn("right", angle)
                    
                else:
                    turn("left", angle)

                continue

        elif person_height > target_maximum_height:
            print_and_log("Person is too close...")
            turn("middle", angle)
            move_backwards()

        else:
            print_and_log("Distance is OK stopping...")
            stop()

        time.sleep(follow_loop_update_time)

# --- Execution ---

if __name__ == "__main__":

    try:
        follow()

    except KeyboardInterrupt:
        stop()
