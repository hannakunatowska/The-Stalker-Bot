
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


def get_distance():
    """
    Return a filtered distance in centimeters.
    - uses median of recent samples
    - rejects single large spikes relative to median
    - falls back to last good reading when appropriate
    """
    global _last_good, _last_good_ts

    raw = get_raw_distance()
    now = _time()

    # append raw reading to buffer
    _buffer.append(raw)

    # compute median of buffer
    med = _median(list(_buffer))

    # if raw is close to median -> accept it
    if abs(raw - med) <= SPIKE_THRESHOLD_CM:
        _last_good = med  # store median as smoothed good value
        _last_good_ts = now
        return round(_last_good, 1)

    # raw significantly differs from median -> treat as spike candidate
    # If the raw is near sensor max (timeout), and median is much smaller,
    # then ignore raw and return last_good (if recent)
    if _last_good is not None and (now - _last_good_ts) <= STALE_TIMEOUT_S:
        # return last good reading (smoothed/median)
        return round(_last_good, 1)

    # Otherwise (no recent good reading) be conservative:
    # return median if median not at max; otherwise return raw (nothing else to rely on)
    if med < (MAX_DISTANCE_CM - 1.0):
        _last_good = med
        _last_good_ts = now
        return round(_last_good, 1)

    # fallback: no good data recently and median is max -> return raw
    return round(raw, 1)


# Optional: simple demo when run directly
if __name__ == "__main__":
    try:
        while True:
            d_raw = get_raw_distance()
            d = get_distance()
            print(f"raw={d_raw:6.1f} cm  filtered={d:6.1f} cm", end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
# --- Execution ---
"""
if __name__ == "__main__":

    while True:
        distance = get_distance()
        print(f"Distance: {distance:.1f} cm", end = "\r")
        time.sleep(distance_loop_update_time)
