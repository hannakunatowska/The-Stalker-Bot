# main_follower.py
import time
import camera_servo
from buttons import press_with_transistor, press_without_transistor

class FollowerBot:
    def __init__(self):
        # constants
        self.turn_time_per_degree = 0.9 / 90  # 0.01 s per degree
        print("FollowerBot initialized.")

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
        # You could also add a backup / side-step here

    def follow(self):
        print("Starting person-follow mode...")
        while True:
            angle, direction, obstacle = camera_servo.get_tracking_data()

            if obstacle:
                self.avoid_obstacle()
                continue

            if direction == "centered":
                if angle and abs(angle - 90) < 10:
                    self.move_forward()
                else:
                    # small steering correction
                    turn_dir = "left" if angle < 90 else "right"
                    self.turn(turn_dir, angle)
            elif direction in ["left", "right"]:
                self.turn(direction, angle)
            else:
                print("No person detected, waiting...")
                self.stop()

            time.sleep(0.2)

if __name__ == "__main__":
    bot = FollowerBot()
    bot.follow()
