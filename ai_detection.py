

# --- Imports ---

import time
import argparse # Imports the argparse module, which provides a way to parse command-line arguments
import sys # Imports the sys module, which provides access to system-specific parameters and functions
from functools import lru_cache # Imports the lru_cache decorator from the functools module, which is used to cache the results of function calls
import cv2 # Imports the OpenCV library for image and video processing
import numpy # Imports the NumPy library for numerical operations on arrays
from gpiozero import Servo # Imports the Servo class from the gpiozero module for controlling servo motors

import libcamera # Imports the libcamera module, which provides access to the camera framework
from picamera2 import MappedArray, Picamera2 # Imports MappedArray and Picamera2 classes for handling camera data and control with the Picamera2 API
from picamera2.devices import IMX500 # Imports the IMX500 device class, representing Sony’s IMX500 image sensor
from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection # Imports NetworkIntrinsics for neural network metadata and postprocess_nanodet_detection for object detection result processing
from picamera2.devices.imx500.postprocess import scale_boxes # Imports the scale_boxes function for adjusting bounding box coordinates to match image dimensions

# --- General definitions ---

main_loop_update_speed = 0.05

obstacle_width_threshold = 0.25 # Sets the obstacle width threshold to 1/4 of the screen width

last_detections = []

ignore_dash_labels = False

camera_frame_width = 640
camera_frame_height = 480
camera_frame_area = camera_frame_width * camera_frame_height

bounding_box_opacity = 0.7
bounding_box_thickness = 2

# --- Servo definitions ---

servo_maximum_position = 1
servo_minimum_position = -1
servo_minimum_pulse_width = 0.5 / 1000
servo_maximum_pulse_width = 2.5 / 1000
servo_step = 0.04
servo_threshold = 0.2
servo_change_threshold = 0.005
servo_smooth_speed = 0.005
servo_step_delay = 0.005

# --- Servo setup ---

servo = Servo(18, min_pulse_width = servo_minimum_pulse_width, max_pulse_width = servo_maximum_pulse_width) # Creates a servo object on GPIO pin 18 with specified pulse widths
servo_position = 0.0 # Creates a variable for the servo position and initializes its value to 0.0 (center position)
servo.value = servo_position # Sets the position to "servo_position"

class Detection:

    """
    Represents a single object detection.

    """

    def __init__(self, coords, category, confidence, metadata):

        """
        Creates a detection object recording the bounding box, the category and the confidence.

        Arguments:
            "coords": The bounding box coordinates (x, y, w, h) as floats in the range [0.0, 1.0]
            "category": The category index as an integer
            "confidence": The confidence score as a float in the range [0.0, 1.0]
            "metadata": The metadata dictionary from the camera

        Returns:
            None

        """

        self.category = category
        self.confidence = confidence
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)


def parse_detections(metadata):

    """
    Parses the output tensor into a number of detected objects, scaled to the ISP output.

    Arguments:
        "metadata": The metadata dictionary from the camera"
    
    Returns:
        "last_detections": A list of detection objects

    """

    global last_detections

    bounding_box_normalization = intrinsics.bbox_normalization # Boolean indicating if bounding boxes are normalized
    bounding_box_order = intrinsics.bbox_order # String indicating the order of bounding box coordinates ("yx" or "xy")

    confidence_threshold = arguments.threshold # Float confidence threshold for filtering detections
    iou = arguments.iou # Float IoU threshold for non-maximum suppression
    max_detections = arguments.max_detections # Integer maximum number of detections to return

    numpy_outputs = imx500.get_outputs(metadata, add_batch = True) # Gets the output tensors from the metadata as a list of NumPy arrays
    input_width, input_height = imx500.get_input_size() # Gets the input size of the model

    if numpy_outputs is None: # If no outputs are available:
        return last_detections # Return the last detections

    if intrinsics.postprocess == "nanodet": # If the postprocessing method is "nanodet":
        boxes, confidence_scores, classes = postprocess_nanodet_detection(outputs = numpy_outputs[0], confidence = confidence_threshold, iou_thres = iou, max_out_dets = max_detections)[0] # Postprocess the outputs using the nanodet method

        boxes = scale_boxes(boxes, 1, 1, input_height, input_width, False, False) # Scale the bounding boxes to the input size

    else: # For other models (e.g., SSD MobileNet):

        boxes, confidence_scores, classes = numpy_outputs[0][0], numpy_outputs[1][0], numpy_outputs[2][0] # Extract boxes, confidence scores, and classes from the outputs

        if bounding_box_normalization: # If bounding boxes are normalized:
            boxes = boxes / input_height # Normalize boxes by input height

        if bounding_box_order == "xy": # If bounding box order is "xy":
            boxes = boxes[:, [1, 0, 3, 2]] # Reorder boxes to "yx" format

        boxes = numpy.array_split(boxes, 4, axis = 1) # Split boxes into separate arrays for y0, x0, y1, x1
        boxes = zip(*boxes) # Unzip the boxes into individual components

    last_detections = []

    for box, confidence_score, category in zip(boxes, confidence_scores, classes): # For every box, confidence score and category:
        if confidence_score > confidence_threshold: # If the confidence score is larger than the confidence threshold:
            detection = Detection(box, category, confidence_score, metadata) # Create a detection object
            last_detections.append(detection) # Add it to "last_detections"

    return last_detections


@lru_cache # Caches the results of the function below (to avoid redundant computations)
def get_labels():

    """
    Gets the labels for the model from intrinsics, filtering out "-" if required.

    Arguments:
        None

    Returns:
        "labels": A list of labels for the model
        "labels_without_dash_labels": The list of labels, but without the dash labels

    """

    labels = intrinsics.labels # Get the labels from intrinsics

    if intrinsics.ignore_dash_labels: # If the ignore_dash_labels flag is set:

        labels_without_dash_labels = []

        for label in labels: # Go through "labels" and remove every "-" label
            if label and label != "-":
                labels_without_dash_labels.append(label)
        
        return labels_without_dash_labels

    return labels

def draw_detections(request, stream = "main"):

    """
    Draws the detections for this request onto the ISP output.
    
    Arguments:
        "request": The Picamera2 request object
        "stream": The stream name to draw on (default: "main")
    
    Returns:
        None

    """

    detections = last_detections # Get the last detection results

    if detections is None:
        return

    labels = get_labels() # Get the labels for the model

    with MappedArray(request, stream) as mapped: # Map the array for the specified stream
        
        for detection in detections: # For each detection:

            x, y, width, height = detection.box # Get the bounding box coordinates

            label = f"{labels[int(detection.category)]} ({detection.confidence:.2f})" # Create the label text with category and confidence

            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1) # Get the size of the text
            text_x = x + 5 # Offset text x-position slightly from the bounding box
            text_y = y + 15 # Offset text y-position slightly from the bounding box

            overlay = mapped.array.copy() # Create a copy of the image array for overlay
            cv2.rectangle(overlay, (text_x, text_y - text_height), (text_x + text_width, text_y + baseline), (255, 255, 255), cv2.FILLED) # Draw a filled rectangle for the text background

            cv2.addWeighted(overlay, 1 - bounding_box_opacity, mapped.array, bounding_box_opacity, 0, mapped.array) # Blend the overlay with the original image
            cv2.putText(mapped.array, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1) # Draw the label text on the image
            cv2.rectangle(mapped.array, (x, y), (x + width, y + height), (0, 255, 0, 0), thickness = bounding_box_thickness) # Draw the bounding box around the detected object

        if intrinsics.preserve_aspect_ratio: # If aspect ratio preservation is enabled:
            box_x, box_y, box_width, box_height = imx500.get_roi_scaled(request) # Get the scaled ROI (Region Of Interest) rectangle from "get_roi_scaled"
            color = (255, 0, 0) # Set its color
            cv2.putText(mapped.array, "ROI", (box_x + 5, box_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1) # Label it
            cv2.rectangle(mapped.array, (box_x, box_y), (box_x + box_width, box_y + box_height), (255, 0, 0, 0)) # Draw it

def get_arguments():

    """
    Gets command line arguments for the script.

    Arguments:
        None

    Returns:
        "arguments": The parsed command line arguments

    """

    parser = argparse.ArgumentParser() # Creates an ArgumentParser object for parsing command-line arguments

    parser.add_argument("--model", type = str, help = "Path of the model", default = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk") # Adds a command-line argument for the model path with a default value

    parser.add_argument("--fps", type = int, help = "Frames per second") # Adds a command-line argument for frames per second

    parser.add_argument("--bounding-box-normalization", action = argparse.BooleanOptionalAction, help = "Normalize bbox") # Adds a command-line argument for bbox normalization

    parser.add_argument("--bounding-box-order", choices = ["yx", "xy"], default = "yx", help = "Set bbox order yx -> (y0, x0, y1, x1) xy -> (x0, y0, x1, y1)") # Adds a command-line argument for bbox order

    parser.add_argument("--threshold", type = float, default = 0.55, help = "Detection threshold") # Adds a command-line argument for detection threshold

    parser.add_argument("--iou", type = float, default = 0.65, help = "Set iou threshold") # Adds a command-line argument for iou threshold

    parser.add_argument("--max-detections", type = int, default = 10, help = "Set max detections") # Adds a command-line argument for max detections

    parser.add_argument("--ignore-dash-labels", action = argparse.BooleanOptionalAction, help = "Remove '-' labels ") # Adds a command-line argument for ignoring dash labels

    parser.add_argument("--postprocess", choices = ["", "nanodet"], default = None, help = "Run post process of type") # Adds a command-line argument for post-processing type

    parser.add_argument("-r", "--preserve-aspect-ratio", action = argparse.BooleanOptionalAction, help = "preserve the pixel aspect ratio of the input tensor") # Adds a command-line argument for preserving aspect ratio

    parser.add_argument("--labels", type = str, help = "Path to the labels file") # Adds a command-line argument for labels file path

    parser.add_argument("--print-intrinsics", action = "store_true", help = "Print JSON network_intrinsics then exit") # Adds a command-line argument for printing intrinsics

    return parser.parse_args()

def update_servo_tracking(x_center_normalized):

    """
    Updates the servo tracking position based on the normalized x center position.

    Arguments:
        x_center_normalized (float): The normalized x center position of the detected object.

    Returns:
        "angle": The calculated servo angle position.

    """

    global servo_position

    direction = None

    target_position = servo_position

    if x_center_normalized > 0.5 + servo_threshold:

        if servo_position > servo_minimum_position:
            target_position = servo_position - servo_step
            direction = "left"

        else:
            direction = "limit reached (left)"

    elif x_center_normalized < 0.5 - servo_threshold:

        if servo_position < servo_maximum_position:
            target_position = servo_position + servo_step
            direction = "right"

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
            time.sleep(servo_step_delay)

    angle = (servo_position + 1) * 90

    print(f"Person x: {x_center_normalized:.2f} | Servo pos: {servo_position:.2f} | Angle: {angle:.1f}° | Direction: {direction}")

    return angle, direction

def get_tracking_data():

    """
    Captures detections, tracks the person and checks for obstacles.

    Arguments:
        None
    
    Returns:
        "angle":
        "direction":
        "obstacle":
        "person_area_normalized":

    """

    last_results = parse_detections(picam2.capture_metadata()) # Gets the latest results by calling "parse_detections"

    person_detections = []

    for detection in last_results:
        if intrinsics.labels[int(detection.category)] == "person":
            person_detections.append(detection) # Collect each person detection in a list

    person_area_normalized = None
    angle, direction = 90, "none"

    if person_detections: # If there are any person detections:
        person = person_detections[0] # Select the first one
        x, _, width, height = person.box # Extract its bounding box data
        x_center = x + width / 2 # Find the horizontal center of the detected person (in pixels)
        x_center_normalized = x_center / camera_frame_width # Converts pixel position into normalized value between 0 and 1
        angle, direction = update_servo_tracking(x_center_normalized) # Updates the servo position by calling "update_servo_tracking" with the normalized x-position
        #person_height_normalized = height / camera_frame_height # Calculates the person height relative to the camera frame height
        person_area_normalized = (width * height) / camera_frame_area

    else: # Else (if there arent any person detections):
        print("No person detected.")

    obstacle_labels = {"chair", "couch", "bed", "bench", "table", "tv", "potted plant","car", "truck", "bottle", "vase", "wall", "refrigerator", "microwave"}
    obstacle_detected = False

    for obstacle in last_results:

        if intrinsics.labels[int(obstacle.category)] in obstacle_labels:
            x, _, width, height = obstacle.box

            if width / camera_frame_width  > obstacle_width_threshold: # If the obstacle box width is larger than the threshold
                label = intrinsics.labels[int(obstacle.category)]
                print(f"Obstacle detected: {label}")
                obstacle_detected = True
                break

    return angle, direction, obstacle_detected, person_area_normalized

# --- Camera setup ---

arguments = get_arguments()
imx500 = IMX500(arguments.model) # Loads the IMX500 camera device and its neural network model file
intrinsics = imx500.network_intrinsics or NetworkIntrinsics() # Retrieves the model’s metadata, and if unavailable, creates a default "NetworkIntrinsics" instance

if not intrinsics.task: # If the task type isn't defined in the model metadata:
    intrinsics.task = "object detection" # Set the task type to "object detection"

picam2 = Picamera2(imx500.camera_num) # Creates a control object for the physical camera

config = picam2.create_preview_configuration( # Creates a preview configuration with:
    controls = {"FrameRate": intrinsics.inference_rate}, # Frame rate from model intrinsics
    buffer_count = 12, # 12 frame buffers (which improves the capture pipeline)
    transform = libcamera.Transform(hflip = True, vflip = True) # Horizontal and vertical flipping
)

picam2.pre_callback = draw_detections # Before each frame is displayed, "draw_detections" is called to overlay bounding boxes and labels
picam2.start(config, show_preview = True) # Starts the video streaming in a live preview window

if intrinsics.preserve_aspect_ratio:
    imx500.set_auto_aspect_ratio()

if __name__ == "__main__":

    print("Starting camera-servo tracking test...")

    try:
        while True:
            angle, direction, obstacle, person_height = get_tracking_data()

            if person_height:
                print(f"Person height (normalized): {person_height:.2f}")

            if obstacle:
                print("Obstacle detected!")
            
            time.sleep(main_loop_update_speed)

    except KeyboardInterrupt:
        print("Stopped by user.")
        picam2.stop()
