# --- Imports ---
from gpiozero import Button, DigitalOutputDevice
from time import sleep

# --- Definitions ---

# Vi använder BOARD-numrering i din originalkod,
# men gpiozero använder BCM som standard.
# Du kan antingen ändra till BCM-nr, eller lägga till pin_factory om du vill använda BOARD.
# Här antar vi att du använder BCM för enkelhetens skull.

move_forward_pin = 22   # motsvarar BOARD 15
move_backwards_pin = 23 # motsvarar BOARD 16
turn_right_pin = 17     # motsvarar BOARD 11
turn_left_pin = 27      # motsvarar BOARD 13

# --- Functions ---

def press_without_transistor(pin):
    """Simulera knapptryck utan transistor"""
    output = DigitalOutputDevice(pin, active_high=True, initial_value=False)
    output.on()   # Sätt HIGH (eller LOW beroende på din krets)
    sleep(0.5)
    output.off()
    output.close()

def press_with_transistor(pin):
    """Simulera knapptryck med transistor"""
    output = DigitalOutputDevice(pin, active_high=False, initial_value=True)
    output.on()
    sleep(0.5)
    output.off()
    output.close()

# --- Testing ---

print("Trying to move forward...")
press_without_transistor(move_forward_pin)

print("Trying to move backwards...")
press_with_transistor(move_backwards_pin)

print("Trying to turn right...")
press_with_transistor(turn_right_pin)

print("Trying to turn left...")
press_without_transistor(turn_left_pin)

print("Testing done!")
