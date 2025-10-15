
# --- Imports ---

import time
import ai_detection
from remote_controller import press
from ultrasonic_sensor import UltrasonicSensor

# --- Definitions ---

turn_time_per_degree = 0.9 / 90
target_minimum_height = 0.45
target_maximum_height = 0.6
safe_distance_in_cm = 40

# --- Setup ---

ultrasonicSensor = UltrasonicSensor(trigger_pin = 23, echo_pin = 24)

# --- Functions ---

def move_forward(press_duration = 0.3):

    """
    Moves the car forward.

    Arguments:
        "press_duration":

    Returns:
        None

    """

    press(22, press_duration)
    print(f"Moved forward for {press_duration} s")

def move_backwards(press_duration = 0.3):
    
    """
    Moves the car backwards.

    Arguments:
        "press_duration":

    Returns:
        None
        
    """

    press(25, press_duration)
    print(f"Moved backwards for {press_duration} s")

def stop():

    """
    Stops the car.

    Arguments:
        None
    
    Returns:
        None

    """

    time.sleep(0.2)

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
        press(17, turn_time)

    if direction == "left":
        press(27, turn_time)
    
    print(f"Turned {direction} for {turn_time:.2f}s (angle {angle:.1f})")

def avoid_obstacle():

    """
    Avoids an obstacle by stopping.

    Arguments:
        None

    Returns:
        None
    
    """

    print("Obstacle detected! Stopping.")
    stop()

def follow():

    """
    Runs the person-following loop.

    Arguments:
        None

    Returns:
        None
    
    """

    while True:

        angle, direction, obstacle, person_height = ai_detection.get_tracking_data() # Gets necessary data from the ai camera

        distance_in_cm = ultrasonicSensor.get_distance() # Gets distance to closest obstacle from ultrasonic sensor
                
        if obstacle:
            avoid_obstacle()
            continue

        if distance_in_cm <= safe_distance_in_cm:
            print("Too close.")
            stop()
            time.sleep(0.5)
            continue
            
        if person_height is None:
            print("No person detected, waiting...")
            stop()
            time.sleep(0.3)
            continue

        # --- Distance logic using person height ---
        print(f"Person height (normalized): {person_height:.2f}")

        if person_height < target_minimum_height:
            print("Person far away → move forward")
            move_forward()

        elif person_height > target_maximum_height:
            print("Person too close → stop")
            stop()

        else:
            print("Distance okay, adjusting heading...")

        # --- Direction logic ---
        if direction == "centered":
            if abs(angle - 90) > 10:
                turn_dir = "left" if angle < 90 else "right"
                turn(turn_dir, angle)
            else:
                print("Centered and aligned.")

        elif direction in ["left", "right"]:
            turn(direction, angle)

        time.sleep(0.2)


if __name__ == "__main__":
    follow()
