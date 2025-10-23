

# --- Imports ---

import time
import ai_detection
from remote_controller import press, unpress, move_backwards_button_pin, move_forward_button_pin, turn_left_button_pin, turn_right_button_pin
from ultrasonic_sensor import get_distance

# --- Definitions ---

turn_time_per_degree = 0.9 / 90
target_minimum_height = 0.45
target_maximum_height = 0.6
safe_distance_in_cm = 40
max_angle_offset = 10
follow_loop_update_time = 0.1

# --- Helper functions ---

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
    press(move_forward_button_pin)

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

    if direction == "right":
        unpress(turn_left_button_pin)
        time.sleep(0.05)
        press(turn_right_button_pin)
        
    if direction == "left":
        unpress(turn_right_button_pin)
        time.sleep(0.05)
        press(turn_left_button_pin)

    if direction == "middle":
        unpress(turn_right_button_pin)
        unpress(turn_left_button_pin)

    print(f"\nTurned {direction} (angle was {angle:.1f})")

def avoid_obstacle():

    """
    Avoids an obstacle by stopping.

    Arguments:
        None

    Returns:
        None
    
    """

    print("\nStopping...")
    stop()

# --- Main program loop ---

def follow():

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
        
        if obstacle or distance_in_cm <= safe_distance_in_cm: # If either the AI camera or the ultrasonic sensor detects an obstacle:
            print("\nTrying to avoid obstacle...")
            turn("middle", angle)
            avoid_obstacle()
            continue
            
        if person_height is None:
            print("\nNo person detected, waiting...")
            turn("middle", angle)
            stop()
            continue

        print(f"\nNormalized person height (Person height / Total frame height) = {person_height:.2f}")

        if person_height < target_minimum_height:

            print("\nPerson is too far away, trying to move forward...")
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
            print("\nPerson is too close...")
            turn("middle", angle)
            move_backwards()

        else:
            print("\nDistance is OK...")

        time.sleep(follow_loop_update_time)

# --- Execution ---

if __name__ == "__main__":

    try:
        follow()

    except KeyboardInterrupt:
        stop()
