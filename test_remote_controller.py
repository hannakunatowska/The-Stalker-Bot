
# --- Imports ---

import lgpio
import time

# --- Definitions ---

button_pins = [22, 23, 17, 27]

move_forward_button_pin = 22
move_backwards_button_pin = 23
turn_right_button_pin = 17
turn_left_button_pin = 27

# --- Setup ---

handle = lgpio.gpiochip_open(0) # Opens GPIO controller 0 and returns a handle

for button_pin in button_pins:
    lgpio.gpio_claim_input(handle, button_pin) # Initializes all pins as inputs

# --- Functions ---

def press_without_transistor(button_pin):
    lgpio.gpio_claim_output(handle, button_pin, 0) # Drive the pin LOW
    time.sleep(0.5) # Wait for half a second
    lgpio.gpio_claim_input(handle, button_pin) # Set the pin to input again (High impedance)

def press_with_transistor(button_pin):
    lgpio.gpio_claim_output(handle, button_pin, 1) # Drive the pin HIGH
    time.sleep(0.5) # Wait for half a second
    lgpio.gpio_claim_input(handle, button_pin) # Set the pin to input again (High impedance)

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

# --- Cleanup ---

lgpio.gpiochip_close(handle) # Closes the GPIO controller