
# --- Imports ---

from gpiozero import DistanceSensor
from collections import deque
import time

# --- Definitions ---

echo_pin = 24
trigger_pin = 23
max_distance_in_m = 2
max_distance_in_cm = max_distance_in_m * 100
distance_loop_update_time = 0.2
buffer_size = 7
spike_threshold_cm = 40 #threshold for a value to differ from the others
timeout = 1.0

# --- Sensor setup ---

ultrasonic_sensor = DistanceSensor(echo = echo_pin, trigger = trigger_pin, max_distance = max_distance_in_m)
print("\nUltrasonic sensor initialized.")
_time = time.time

# --- Internal state ---
_buffer = deque(maxlen = buffer_size)   # stores recent raw cm readings
_last_good = None                      # last accepted (filtered) reading in cm
_last_good_time = 0.0

# Pre-fill buffer with max distance so median is conservative at start
for _ in range(buffer_size):
    _buffer.append(max_distance_in_cm)

# --- Functions ---

def get_raw_distance():

    """
    Gets the distance from the ultrasonic sensor.

    Arguments:
        None
    
    Returns:
        "distance_in_cm": The distance in centimeters.

    """

    distance_in_m = ultrasonic_sensor.distance  # Returns a value between 0.0 and 1.0 (relative to max_distance)
    distance_in_cm = distance_in_m * 100

    return round(distance_in_cm, 1)

def _median(data):
    s = sorted(data)
    middle = len(s) // 2
    if len(s) % 2 == 1:
        return s[middle]
    return 0.5 * (s[middle-1] + s[middle])

# --- Execution ---

if __name__ == "__main__":

    while True:
        distance = get_distance()
        print(f"Distance: {distance:.1f} cm", end = "\r")
        time.sleep(distance_loop_update_time)
