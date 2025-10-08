from gpiozero import Motor
from time import sleep

# --- Motor setup ---
# Map your pins to Motor objects
# Adjust forward/backward pins according to your wiring
forward_motor = Motor(forward=5, backward=6)
turn_motor = Motor(forward=13, backward=19)

# --- Functions ---
def all_stop():
    forward_motor.stop()
    turn_motor.stop()

def move_forward(duration=1):
    print("Moving forward")
    all_stop()
    forward_motor.forward()
    sleep(duration)
    all_stop()

def move_backward(duration=1):
    print("Moving backward")
    all_stop()
    forward_motor.backward()
    sleep(duration)
    all_stop()

def turn_left(duration=0.5):
    print("Turning left")
    all_stop()
    turn_motor.forward()
    sleep(duration)
    all_stop()

def turn_right(duration=0.5):
    print("Turning right")
    all_stop()
    turn_motor.backward()
    sleep(duration)
    all_stop()

# --- Example test sequence ---
try:
    move_forward(2)
    turn_left(1)
    move_backward(2)
    turn_right(1)
    all_stop()

except KeyboardInterrupt:
    all_stop()
    print("Interrupted!")