from gpiozero import DistanceSensor
import time

class UltrasonicSensor:
    def __init__(self, echo_pin=24, trigger_pin=23, max_distance=2.0, threshold=0.3):
        """
        Initializes an ultrasonic sensor using gpiozero.

        Args:
            echo_pin (int): GPIO pin for echo (input)
            trigger_pin (int): GPIO pin for trigger (output)
            max_distance (float): Maximum measurable distance in meters (default 2m)
            threshold (float): Distance threshold in meters for obstacle detection
        """
        self.sensor = DistanceSensor(
            echo=echo_pin,
            trigger=trigger_pin,
            max_distance=max_distance,
            threshold_distance=threshold
        )
        print(f"Ultrasonic sensor initialized (trigger={trigger_pin}, echo={echo_pin})")

    def get_distance(self):
        """Returns the current distance in centimeters."""
        distance_m = self.sensor.distance  # Returns value between 0 and 1 (as a fraction of max_distance)
        distance_cm = distance_m * 100
        return round(distance_cm, 1)

    def is_obstacle(self, limit_cm=30):
        """
        Checks if an obstacle is within the given limit (default 30 cm).
        Returns True if obstacle detected.
        """
        dist = self.get_distance()
        return dist <= limit_cm

if __name__ == "__main__":
    ultra = UltrasonicSensor(echo_pin=24, trigger_pin=23)

    try:
        while True:
            dist = ultra.get_distance()
            print(f"Distance: {dist:.1f} cm", end="\r")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nStopped.")
