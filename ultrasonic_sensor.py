# --- Imports ---
from gpiozero import DistanceSensor
import time

# --- Definitions ---
echo_pin = 24
trigger_pin = 23
max_distance_in_m = 2
max_distance_in_cm = max_distance_in_m * 100
distance_loop_update_time = 0.1
timeout = 0.3  # seconds: how long to trust the last valid reading
spike_threshold = 20  # cm, any sudden jump larger than this is ignored

# --- Sensor setup ---
ultrasonic_sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, max_distance=max_distance_in_m)
print("\nUltrasonic sensor initialized.")

# --- Internal state ---
_last_valid = max_distance_in_cm
_last_time = time.time()

# --- Functions ---
def get_distance():
    global _last_valid, _last_time

    raw = ultrasonic_sensor.distance * 100  #gets the distance from the sensor
    now = time.time()

    # Accept if difference is reasonable
    if abs(raw - _last_valid) <= spike_threshold:
        _last_valid = raw
        _last_time = now
        return round(_last_valid, 1)

    # Otherwise check if last valid reading is recent enough
    if now - _last_time <= timeout:
        return round(_last_valid, 1)

    # Spike persists too long, accept new reading
    _last_valid = raw
    _last_time = now
    return round(_last_valid, 1)

# --- Demo ---
if __name__ == "__main__":
    try:
        while True:
            dist = get_distance()
            print(f"Filtered distance: {dist:.1f} cm", end="\r")
            time.sleep(distance_loop_update_time)
    except KeyboardInterrupt:
        print("\nStopped.")
