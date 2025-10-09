# --- imports ---
from ai_detection import update_servo_tracking, parse_detections, imx500, intrinsics
from buttons import move_forward, move_backward, turn_left, turn_right, all_stop
from picamera2 import Picamera2
import time

# --- Setup camera ---
picam2 = Picamera2(imx500.camera_num)
config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12)
picam2.start(config, show_preview=True)

# --- main loop ---
try:
    while True:
        # Capture AI detection metadata from the camera
        # This data includes all objects the AI model has detected
        detections = parse_detections(picam2.capture_metadata())
        person_detections = [d for d in detections if intrinsics.labels[int(d.category)] == "person"]

        if person_detections:
            person = person_detections[0] # Take the first detected person
            x, y, w, h = person.box # Extract position and size from the bounding box
            x_center = x + w / 2 # Calculate horizontal center of the person
            frame_width = picam2.stream_configuration("main")["size"][0] # Get the total width of the frame to normalize position
            x_center_normalized = x_center / frame_width # Normalize x_center (0 = far left, 1 = far right)

            # This function prints direction internally
            angle = update_servo_tracking(x_center_normalized)

            # Decide motion based on servo direction
            if 80 <= angle <= 100: # If the person is roughly centered (angle ~90°), move forward
                move_forward(0.5)
            elif angle < 80: # If the person is to the left of the frame, turn left
                turn_left(0.3)
            elif angle > 100:  # If the person is to the right of the frame, turn right
                turn_right(0.3)
        else:
            all_stop()   # If no person detected, stop all movement

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopped by user.")
    all_stop()