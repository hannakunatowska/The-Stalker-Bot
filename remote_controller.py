
# --- Imports ---

import lgpio
import time

# --- Definitions ---

button_pins = [17, 22, 25, 27]

move_forward_button_pin = 22
move_backwards_button_pin = 25
turn_right_button_pin = 17
turn_left_button_pin = 27

# --- Setup ---

handle = lgpio.gpiochip_open(0) # Opens GPIO controller 0 and returns a handle

for button_pin in button_pins:
    lgpio.gpio_claim_input(handle, button_pin) # Initializes all pins as inputs

# --- Functions ---

def press(button_pin, press_duration = 0.1):
    lgpio.gpio_claim_output(handle, button_pin, 1) # Drive the pin HIGH
    time.sleep(press_duration) # Wait
    lgpio.gpio_claim_input(handle, button_pin) # Set the pin to input again (high impedance)