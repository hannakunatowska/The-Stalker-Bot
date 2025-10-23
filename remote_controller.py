
# --- Imports ---

import lgpio

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

def press(button_pin):

    """
    Simulates a button press by driving the GPIO pin HIGH.
    
    Arguments:
        "button_pin": The GPIO pin of the button to press.
        
    Returns:
        None
    
    """

    lgpio.gpio_claim_output(handle, button_pin, 1) # Drive the pin HIGH

def unpress(button_pin):

    """
    Simulates a button release by setting the GPIO pin to input (high impedance).
    
    Arguments:
        "button_pin": The GPIO pin of the button to release.
        
    Returns:
        None
    
    """

    lgpio.gpio_claim_input(handle, button_pin) # Set the pin to input (high impedance)

def check_button_press(button_pin):

    """
    Checks if a button is pressed.
    
    Arguments:
        "button_pin": The GPIO pin of the button to check.
    
    Returns:
        True if the button is pressed, False otherwise.
    
    """

    return lgpio.gpio_read(handle, button_pin) == 1 # Returns True if the pin is HIGH (button pressed), else False