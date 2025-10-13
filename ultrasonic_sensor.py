from gpiozero import DistanceSensor
import time

class UltrasonicSensor:
    def __init__(self, echo_pin=24, trigger_pin=23, max_distance=2.0):
        """
        Simple ultrasonic sensor class using gpiozero.

        Args:
            echo_pin (int): GPIO pin for echo (input)
            trigger_pin (int): GPIO pin for trigger (output)
            max_distance (float): Maximum measurable distance in meters (default 2m)
        """
        self.sensor = DistanceSensor(
            echo=echo_pin,
            trigger=trigger_pin,
            max_distance=max_distance
        )
        print(f"Ultrasonic sensor initialized (trigger={trigger_pin}, echo={echo_pin})")

    def get_distance(self):
        """
        Returns the current measured distance in centimeters.
        """
        distance_m = self.sensor.distance  # Returns a value between 0.0 and 1.0 (relative to max_distance)
        distance_cm = distance_m * 100
        return round(distance_cm, 1)

if __name__ == "__main__":
    sensor = UltrasonicSensor(echo_pin=24, trigger_pin=23)

    try:
        while True:
            dist = sensor.get_distance()
            print(f"Distance: {dist:.1f} cm", end="\r")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nStopped.")
