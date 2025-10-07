import RPi.GPIO as GPIO
import time

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define motor control pins
motors = {
    "forward": 5,
    "backward": 6,
    "left": 13,
    "right": 19
}

# Setup pins as outputs
for pin in motors.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def all_stop():
    for pin in motors.values():
        GPIO.output(pin, GPIO.LOW)

def move_forward(duration=1):
    print("Moving forward")
    all_stop()
    GPIO.output(motors["forward"], GPIO.HIGH)
    time.sleep(duration)
    all_stop()

def move_backward(duration=1):
    print("Moving backward")
    all_stop()
    GPIO.output(motors["backward"], GPIO.HIGH)
    time.sleep(duration)
    all_stop()

def turn_left(duration=0.5):
    print("Turning left")
    all_stop()
    GPIO.output(motors["left"], GPIO.HIGH)
    time.sleep(duration)
    all_stop()

def turn_right(duration=0.5):
    print("Turning right")
    all_stop()
    GPIO.output(motors["right"], GPIO.HIGH)
    time.sleep(duration)
    all_stop()

# --- Example test sequence ---
try:
    move_forward(2)
    turn_left(1)
    move_backward(2)
    turn_right(1)
    all_stop()

except KeyboardInterrupt:
    pass

finally:
    print("Cleaning up GPIO...")
    all_stop()
    GPIO.cleanup()
