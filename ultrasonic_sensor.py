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

# Buffer / filtering params
buffer_size = 7
spike_threshold_cm = 40.0   # threshold for a reading to be considered a spike vs median
timeout = 1.0               # seconds: how long we trust the last good reading
max_spike_count = 2         # how many consecutive spikes before accepting them
verbose = False             # set True to print debug info

# --- Sensor setup ---
ultrasonic_sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, max_distance=max_distance_in_m)
print("\nUltrasonic sensor initialized.")
_time = time.time

# --- Internal state ---
_buffer = deque(maxlen=buffer_size)   # stores recent raw cm readings
_last_good = None                      # last accepted (filtered) reading in cm
_last_good_time = 0.0
_spike_count = 0

# Pre-fill buffer with max distance so median is conservative at start
for _ in range(buffer_size):
    _buffer.append(max_distance_in_cm)

# --- Functions ---
def get_raw_distance():
    """
    Gets the raw distance from the ultrasonic sensor in centimeters.
    """
    # DistanceSensor.distance returns 0.0..1.0 relative to max_distance
    distance_in_m = ultrasonic_sensor.distance
    distance_in_cm = distance_in_m * 100.0
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
    - rejects isolated large spikes (e.g. timeouts at max range)
    - accepts a spike only if it persists for `max_spike_count` consecutive samples
    - falls back to last good reading if recent
    """
    global _last_good, _last_good_time, _spike_count

    raw = get_raw_distance()
    now = _time()

    # compute median of buffer (buffer contains previous samples)
    med = _median(list(_buffer))

    # decide if this raw reading is a spike relative to the median
    is_spike = abs(raw - med) > spike_threshold_cm

    if verbose:
        print(f"[US] raw={raw:.1f} med={med:.1f} last_good={_last_good} spike={is_spike} spike_cnt={_spike_count}")

    if is_spike:
        _spike_count += 1

        # If we have a recent reliable value, ignore short spikes
        if _last_good is not None and (now - _last_good_time) <= timeout:
            if _spike_count <= max_spike_count:
                # keep returning the last good value and append last_good to buffer to maintain stability
                _buffer.append(_last_good)
                return round(_last_good, 1)
            else:
                # spike persisted long enough; accept spike (but still append raw)
                _buffer.append(raw)
                _last_good = raw
                _last_good_time = now
                _spike_count = 0
                return round(_last_good, 1)
        else:
            # No recent good value — be conservative:
            # use median if median isn't at max; otherwise accept raw
            if med < (max_distance_in_cm - 1.0):
                _buffer.append(med)
                _last_good = med
                _last_good_time = now
                _spike_count = 0
                return round(_last_good, 1)
            else:
                # nothing reliable — accept raw (sensor may genuinely report max)
                _buffer.append(raw)
                _last_good = raw
                _last_good_time = now
                _spike_count = 0
                return round(_last_good, 1)
    else:
        # not a spike — accept and reset spike counter
        _spike_count = 0
        _buffer.append(raw)
        # update last good as median for smoothing
        smoothed = _median(list(_buffer))
        _last_good = smoothed
        _last_good_time = now
        return round(_last_good, 1)

# Optional: simple demo when run directly
if __name__ == "__main__":
    try:
        print("Running ultrasonic demo (Ctrl+C to stop).")
        while True:
            distance_raw = get_raw_distance()
            distance = get_distance()
            print(f"raw={distance_raw:6.1f} cm  filtered={distance:6.1f} cm", end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
