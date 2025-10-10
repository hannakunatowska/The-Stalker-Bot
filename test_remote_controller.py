
# --- Imports ---

import RPi.GPIO as GPIO
import time

# --- Definitions ---

button_pins = [11, 13, 15, 16]

move_forward_button_pin = 15
move_backwards_button_pin = 16
turn_right_button_pin = 11
turn_left_button_pin = 13

# --- Setup ---

GPIO.setmode(GPIO.BOARD)

for button_pin in button_pins:
    GPIO.setup(button_pin, GPIO.IN)

# --- Functions ---

def press_without_transistor(button_pin):
    GPIO.setup(button_pin, GPIO.OUT, initial = GPIO.LOW)
    time.sleep(0.5)
    GPIO.setup(button_pin, GPIO.IN)

def press_with_transistor(button_pin):
    GPIO.setup(button_pin, GPIO.OUT, initial = GPIO.HIGH)
    time.sleep(0.5)
    GPIO.setup(button_pin, GPIO.IN)

# --- Testing ---

print("Trying to move forward...")

press_without_transistor(move_forward_button_pin)

print("Trying to move backwards...")

press_with_transistor(move_backwards_button_pin)

print("Trying to turn right...")

press_with_transistor(turn_right_button_pin)

print("Trying to turn left...")

press_without_transistor(turn_left_button_pin)

print("Testing done!")

GPIO.cleanup()