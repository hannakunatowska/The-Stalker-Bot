
# --- Imports ---

from gpiozero import DistanceSensor
import time

# --- Definitions ---

echo_pin = 24
trigger_pin = 23
max_distance_in_m = 2
distance_loop_update_time = 0.2
buffer_size = 7


# --- Sensor setup ---

ultrasonicSensor = DistanceSensor(echo = echo_pin, trigger = trigger_pin, max_distance = max_distance_in_m)

print("\nUltrasonic sensor initialized.")

# --- Functions ---

def get_distance():

    """
    Gets the distance from the ultrasonic sensor.

    Arguments:
        None
    
    Returns:
        "distance_in_cm": The distance in centimeters.

    """

    distance_in_m = ultrasonicSensor.distance  # Returns a value between 0.0 and 1.0 (relative to max_distance)
    distance_in_cm = distance_in_m * 100

    return round(distance_in_cm, 1)

# --- Execution ---

if __name__ == "__main__":

    while True:
        distance = get_distance()
        print(f"Distance: {distance:.1f} cm", end = "\r")
        time.sleep(distance_loop_update_time)
