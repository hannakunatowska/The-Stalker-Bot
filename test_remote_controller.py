
# --- Imports ---

import lgpio
import time

# --- Definitions ---

button_pins = [17, 22, 23, 27]

move_forward_button_pin = 22
move_backwards_button_pin = 23
turn_right_button_pin = 17
turn_left_button_pin = 27

# --- Setup ---

handle = lgpio.gpiochip_open(0) # Opens GPIO controller 0 and returns a handle

for button_pin in button_pins:
    lgpio.gpio_claim_input(handle, button_pin) # Initializes all pins as inputs

# --- Functions ---

def press(button_pin):
    lgpio.gpio_claim_output(handle, button_pin, 1) # Drive the pin HIGH
    time.sleep(0.5) # Wait for half a second
    lgpio.gpio_claim_input(handle, button_pin) # Set the pin to input again (high impedance)

# --- Testing ---

print("Trying to move forward...")

press(move_forward_button_pin)
time.sleep(1)
press(move_forward_button_pin)
time.sleep(1)

print("Trying to move backwards...")

press(move_backwards_button_pin)
time.sleep(1)
press(move_backwards_button_pin)
time.sleep(1)

print("Trying to turn right...")

press(turn_right_button_pin)
time.sleep(1)
press(turn_right_button_pin)
time.sleep(1)

print("Trying to turn left...")

press(turn_left_button_pin)
time.sleep(1)
press(turn_left_button_pin)
time.sleep(1)

print("Testing done!")

# --- Cleanup ---

lgpio.gpiochip_close(handle) # Closes the GPIO controller