# main_follower.py
import time
import camera_servo
from buttons import press_with_transistor, press_without_transistor
from ultrasonic_sensor import UltrasonicSensor

class FollowerBot:
    def __init__(self):
        # constants
        self.turn_time_per_degree = 0.9 / 90  # 0.01 s per degree
        self.target_min_height = 0.45  # too far
        self.target_max_height = 0.60  # too close
        self.safe_distance_cm = 40  
        print("FollowerBot initialized.")

        self.ultra = UltrasonicSensor(trigger_pin=23, echo_pin=24)

    def move_forward(self, duration=0.3):
        print("Moving forward")
        press_without_transistor(22)
        time.sleep(duration)

    def stop(self):
        print("Stop")
        time.sleep(0.2)

    def turn(self, direction, angle):
        turn_pin = 17 if direction == "right" else 27
        press_func = press_with_transistor if direction == "right" else press_without_transistor
        turn_time = abs(angle - 90) * self.turn_time_per_degree
        print(f"↪️ Turning {direction} for {turn_time:.2f}s (angle {angle:.1f})")
        press_func(turn_pin)
        time.sleep(turn_time)

    def avoid_obstacle(self):
        print("Obstacle detected! Stopping.")
        self.stop()

    def follow(self):
        print("Starting person-follow mode...")
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
