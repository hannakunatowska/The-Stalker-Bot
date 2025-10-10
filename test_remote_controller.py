
# --- Imports ---

import RPi.GPIO as GPIO
import time

# --- Definitions ---

button_pins = []

move_forward_button_pin =
move_backwards_button_pin =
turn_right_button_pin =
turn_left_button_pin =

# --- Setup ---

GPIO.setmode(GPIO.BCM)

for button_pin in button_pins:
    GPIO.setup(button_pin, GPIO.IN)

# --- Functions ---

def press(button_pin):
    GPIO.setup(button_pin, GPIO.OUT, initial = GPIO.LOW)
    time.sleep(0.5)
    GPIO.setup(button_pin, GPIO.IN)

# --- Testing ---

print("Trying to move forward...")

press(move_forward_button_pin)

print("Trying to move backwards...")

press(move_backwards_button_pin)

print("Trying to turn right...")

press(turn_right_button_pin)

print("Trying to turn left...")

press(turn_left_button_pin)

print("Testing done!")

GPIO.cleanup()