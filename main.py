

# --- Imports ---

import time
import ai_detection
from remote_controller import press, unpress, button_pins
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

    press(22)

def move_backwards():

    """
    Moves the car backwards.

    Arguments:
        "press_duration": The duration of the simulated button press (default set to 0.3 s).

    Returns:
        None
        
    """

    press(25)

def stop():

    """
    Stops the car.

    Arguments:
        None
    
    Returns:
        None

    """

    for button_pin in button_pins:
        unpress(button_pin)

def turn(direction, angle):

    """
    Turns the car.

    Arguments:
        "direction": The turning direction.
        "angle": The angle to the person.

    Returns:
        None
    
    """

    turn_time = abs(angle - 90) * turn_time_per_degree # Sets the turning time by multiplying the angle by "turn_time_per_degree"

    if direction == "right":
        press(17)
        time.sleep(turn_time)
        unpress(17)
        
    if direction == "left":
        press(27)
        time.sleep(turn_time)
        unpress(27)
        
    print(f"\nTurned {direction} for {turn_time:.2f}s (angle was {angle:.1f})")

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
            avoid_obstacle()
            continue
            
        if person_height is None:
            print("\nNo person detected, waiting...")
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
            
            elif direction in ("limit reached (left)", "limit reached (right)"):

                if angle < 90:
                    turn("right", angle)
                    
                else:
                    turn("left", angle)

        elif person_height > target_maximum_height:
            print("\nPerson is too close...")
            move_backwards()
            time.sleep(0.5)
            stop()

        else:
            print("\nDistance is OK...")

        time.sleep(follow_loop_update_time)

# --- Execution ---

if __name__ == "__main__":

    try:
        follow()

    except KeyboardInterrupt:
        stop()