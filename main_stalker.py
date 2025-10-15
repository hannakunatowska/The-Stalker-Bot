
# --- Imports ---

import time
import camera_servo
from remote_controller import press
from ultrasonic_sensor import UltrasonicSensor

class FollowerBot:

    def __init__(self):

        self.turn_time_per_degree = 0.9 / 90  # 0.01 s per degree
        self.target_min_height = 0.45  # too far
        self.target_max_height = 0.60  # too close
        self.safe_distance_cm = 40  
        print("FollowerBot initialized.")

        self.ultra = UltrasonicSensor(trigger_pin = 23, echo_pin = 24)

    def move_forward(self, press_duration = 0.3):
        press(22, press_duration)
        print(f"Moved forward for {press_duration} s")

    def stop(self):
        print("Stop")
        time.sleep(0.2)

    def turn(self, direction, angle):

        """
        Turns the car.

        Arguments:
            "direction":
            "angle":

        Returns:
            None
        
        """

        turn_time = abs(angle - 90) * self.turn_time_per_degree

        if direction == "right":
            press(17, turn_time)

        else:
            press(27, turn_time)
        
        print(f"Turned {direction} for {turn_time:.2f}s (angle {angle:.1f})")

    def avoid_obstacle(self):
        print("Obstacle detected! Stopping.")
        self.stop()

    def follow(self):

        """
        Runs the person-following loop.

        Arguments:
            None

        Returns:
            None
        
        """

        while True:
            angle, direction, obstacle, person_height = camera_servo.get_tracking_data()

            distance_cm = self.ultra.get_distance()
            too_close = distance_cm <= self.safe_distance_cm
            
            if obstacle:
                self.avoid_obstacle()
                continue

            if too_close:
                print("Too close.")
                self.stop()
                time.sleep(0.5)
                continue
                
            if person_height is None:
                print("No person detected, waiting...")
                self.stop()
                time.sleep(0.3)
                continue

            # --- Distance logic using person height ---
            print(f"Person height (normalized): {person_height:.2f}")

            if person_height < self.target_min_height:
                print("Person far away → move forward")
                self.move_forward()
            elif person_height > self.target_max_height:
                print("Person too close → stop")
                self.stop()
            else:
                print("Distance okay, adjusting heading...")

            # --- Direction logic ---
            if direction == "centered":
                if abs(angle - 90) > 10:
                    turn_dir = "left" if angle < 90 else "right"
                    self.turn(turn_dir, angle)
                else:
                    print("Centered and aligned.")
            elif direction in ["left", "right"]:
                self.turn(direction, angle)

            time.sleep(0.2)


if __name__ == "__main__":
    bot = FollowerBot()
    bot.follow()
