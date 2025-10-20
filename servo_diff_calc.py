from gpiozero import Servo # Imports the Servo class from the gpiozero module for controlling servo motors
import ai_detection


# --- Definitions ---

servo_maximum_position = 1
servo_minimum_position = -1
servo_minimum_pulse_width = 0.5 / 1000
servo_maximum_pulse_width = 2.5 / 1000
servo_step = 0.04
servo_threshold = 0.07
servo_change_threshold = 0.005
servo_smooth_speed = 0.005

x_center_norm = 0

# --- Servo setup ---

servo = Servo(18, min_pulse_width = servo_minimum_pulse_width, max_pulse_width = servo_maximum_pulse_width) # Creates a servo object on GPIO pin 18 with specified pulse widths
servo_position = 0.0 # Creates a variable for the servo position and initializes its value to 0.0 (center position)
servo.value = servo_position # Sets the position to "servo_position"


def servo_diff():

	global servo_position

	x_center_norm = ai_detection.x_center_normalized

	direction = None

	target_position = servo_position


	if x_center_normalized > 0.5 + servo_threshold:

		if servo_position > servo_minimum_position:
			target_position = servo_position - servo_step
			direction = "left"
			
			#calc angle
			
		else:
			direction = "limit reached (left)"

	elif x_center_normalized < 0.5 - servo_threshold:

		if servo_position < servo_maximum_position:
			target_position = servo_position + servo_step
			direction = "right"
			
			#calc angle
			
			
			
		else:
			direction = "limit reached (right)"
			
	else: # Else (if the person is roughly in the middle):
		direction = "centered" # Set direction to "centered"

	target_position = max(servo_minimum_position, min(servo_maximum_position, target_position))

	if abs(target_position - servo_position) >= servo_change_threshold:

		servo_steps = int(abs(target_position - servo_position) / servo_smooth_speed)

		if target_position > servo_position:
			direction_sign = 1

		else:
			direction_sign = -1

		for _ in range(servo_steps):
			servo_position += direction_sign * servo_smooth_speed
			servo.value = servo_position
			time.sleep(0.005)

	angle = (servo_position + 1) * 90

	print(f"Person x: {x_center_normalized:.2f} | Servo pos: {servo_position:.2f} | Angle: {angle:.1f}° | Direction: {direction}")

	return angle, direction

