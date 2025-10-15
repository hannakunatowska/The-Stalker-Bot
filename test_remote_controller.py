
# --- Imports ---

import lgpio
import time
from remote_controller import button_pins, move_forward_button_pin, move_backwards_button_pin, turn_left_button_pin, turn_right_button_pin, press

# --- Setup ---

handle = lgpio.gpiochip_open(0) # Opens GPIO controller 0 and returns a handle

for button_pin in button_pins:
    lgpio.gpio_claim_input(handle, button_pin) # Initializes all pins as inputs

# --- Testing ---

print("\nTrying to move forward...")

press(move_forward_button_pin)
time.sleep(1)
press(move_forward_button_pin)
time.sleep(1)

print("\nTrying to move backwards...")

press(move_backwards_button_pin)
time.sleep(1)
press(move_backwards_button_pin)
time.sleep(1)

print("\nTrying to turn right...")

press(turn_right_button_pin)
time.sleep(1)
press(turn_right_button_pin)
time.sleep(1)

print("\nTrying to turn left...")

press(turn_left_button_pin)
time.sleep(1)
press(turn_left_button_pin)
time.sleep(1)

print("\nTesting done!\n")

# --- Cleanup ---

lgpio.gpiochip_close(handle) # Closes the GPIO controller