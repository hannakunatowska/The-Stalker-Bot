
# --- Imports ---

import argparse # Imports the argparse module, which provides a way to parse command-line arguments
import sys # Imports the sys module, which provides access to system-specific parameters and functions
from functools import lru_cache # Imports the lru_cache decorator from the functools module, which is used to cache the results of function calls
import cv2 # Imports the OpenCV library for image and video processing
import numpy as np # Imports the NumPy library for numerical operations on arrays

from picamera2 import MappedArray, Picamera2 # Imports MappedArray and Picamera2 classes from the picamera2 module for camera operations
from picamera2.devices import IMX500 # Imports the IMX500 class from the picamera2.devices module for using the IMX500 camera
from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection # Imports NetworkIntrinsics and postprocess_nanodet_detection from the imx500 module
from picamera2.devices.imx500.postprocess import scale_boxes # Imports the scale_boxes function from the postprocess module for scaling bounding boxes

from gpiozero import Servo # Imports the Servo class from the gpiozero module for controlling servo motors
import time # Imports the time module for time-related functions

# --- Definitions ---

last_detections = []

# --- Setup ---

servo = Servo(18, min_pulse_width = 0.5 / 1000, max_pulse_width = 2.5 / 1000) # Creates a Servo object on GPIO pin 18 with specified pulse widths
servo_position = 0.0  # Creates a variable for the servo position and initializes its value to 0.0 (center position)
servo.value = servo_position # Sets the position to "servo_position"

class Detection:

    """
    Represents a single object detection.

    """

    def __init__(self, coords, category, conf, metadata):

        """
        Creates a Detection object recording the bounding box, category and confidence.

        Arguments:
            "coords": The bounding box coordinates (x, y, w, h) as floats in the range [0.0, 1.0]
            "category": The category index as an integer
            "conf": The confidence score as a float in the range [0.0, 1.0]
            "metadata": The metadata dictionary from the camera

        Returns:
            None

        """

        self.category = category # Integer category index
        self.conf = conf # Float confidence score
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)

def parse_detections(metadata: dict):

    """
    Parse the output tensor into a number of detected objects, scaled to the ISP output.

    Arguments:
        "metadata": The metadata dictionary from the camera"
    
    Returns:
        "last_detections": A list of Detection objects

    """

    global last_detections

    bbox_normalization = intrinsics.bbox_normalization # Boolean indicating if bounding boxes are normalized
    bbox_order = intrinsics.bbox_order # String indicating the order of bounding box coordinates ("yx" or "xy")

    threshold = args.threshold # Float confidence threshold for filtering detections
    iou = args.iou # Float IoU threshold for non-maximum suppression
    max_detections = args.max_detections # Integer maximum number of detections to return

    np_outputs = imx500.get_outputs(metadata, add_batch = True) # Gets the output tensors from the metadata as a list of NumPy arrays
    input_w, input_h = imx500.get_input_size() # Gets the input size of the model

    if np_outputs is None: # If no outputs are available:
        return last_detections # Return the last detections
    
    if intrinsics.postprocess == "nanodet": # If the postprocessing method is "nanodet":

        boxes, scores, classes = \
            postprocess_nanodet_detection(outputs = np_outputs[0], conf = threshold, iou_thres = iou, max_out_dets = max_detections)[0] # Postprocess the outputs using the nanodet method
        
        boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False) # Scale the bounding boxes to the input size

    else: # For other models (e.g., SSD MobileNet):

        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0] # Extract boxes, scores, and classes from the outputs

        if bbox_normalization: # If bounding boxes are normalized:
            boxes = boxes / input_h # Normalize boxes by input height

        if bbox_order == "xy": # If bounding box order is "xy":
            boxes = boxes[:, [1, 0, 3, 2]] # Reorder boxes to "yx" format

        boxes = np.array_split(boxes, 4, axis = 1) # Split boxes into separate arrays for y0, x0, y1, x1
        boxes = zip(*boxes) # Unzip the boxes into individual components

    last_detections = [
        Detection(box, category, score, metadata) # Create a Detection object for each valid detection
        for box, score, category in zip(boxes, scores, classes) # Iterate over boxes, scores, and categories
        if score > threshold # Filter detections by confidence threshold
    ]

    return last_detections


@lru_cache # Cache the results of this function to avoid redundant computations

def get_labels():

    """
    Gets the labels for the model from intrinsics, filtering out "-" if required.

    Arguments:
        None

    Returns:
        "labels": A list of labels for the model

    """

    labels = intrinsics.labels # Get the labels from intrinsics

    if intrinsics.ignore_dash_labels: # If the ignore_dash_labels flag is set:
        labels = [label for label in labels if label and label != "-"] # Filter out empty and "-" labels

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

    detections = last_results # Get the last detection results

    if detections is None:
        return
    
    labels = get_labels() # Get the labels for the model

    with MappedArray(request, stream) as m: # Map the array for the specified stream

        for detection in detections: # Iterate over each detection

            x, y, w, h = detection.box # Get the bounding box coordinates
            label = f"{labels[int(detection.category)]} ({detection.conf:.2f})" # Create the label text with category and confidence

            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1) # Get the size of the text
            text_x = x + 5 # Offset text position slightly from the bounding box
            text_y = y + 15 # Offset text position slightly from the bounding box

            overlay = m.array.copy() # Create a copy of the image array for overlay

            cv2.rectangle(overlay, (text_x, text_y - text_height), (text_x + text_width, text_y + baseline), (255, 255, 255), cv2.FILLED) # Draw a filled rectangle for the text background

            alpha = 0.30 # Transparency factor

            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array) # Blend the overlay with the original image

            cv2.putText(m.array, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1) # Draw the label text on the image

            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness = 2) # Draw the bounding box around the detected object

        if intrinsics.preserve_aspect_ratio: # If aspect ratio preservation is enabled:

            b_x, b_y, b_w, b_h = imx500.get_roi_scaled(request) # Get the scaled region of interest (ROI)
            color = (255, 0, 0) # Set the color for the ROI rectangle

            cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1) # Label the ROI
            cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0)) # Draw the ROI rectangle


def get_args():

    """
    Gets command line arguments for the script.

    Arguments:
        None

    Returns:
        "args": The parsed command line arguments

    """

    parser = argparse.ArgumentParser() # Creates an ArgumentParser object for parsing command-line arguments

    parser.add_argument("--model", type = str, help = "Path of the model", default = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk") # Adds a command-line argument for the model path with a default value

    parser.add_argument("--fps", type = int, help = "Frames per second") # Adds a command-line argument for frames per second

    parser.add_argument("--bbox-normalization", action = argparse.BooleanOptionalAction, help = "Normalize bbox") # Adds a command-line argument for bbox normalization

    parser.add_argument("--bbox-order", choices = ["yx", "xy"], default = "yx", help = "Set bbox order yx -> (y0, x0, y1, x1) xy -> (x0, y0, x1, y1)") # Adds a command-line argument for bbox order

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

    threshold = 0.07
    step = 0.05
    change_threshold = 0.01
    max_pos = 1.0
    min_pos = -1.0
    direction = None
    
    new_pos = servo_position

    if x_center_normalized > 0.5 + threshold:

        if servo_position > min_pos:
            new_pos = servo_position - step
            direction = "left"

        else:
            direction = "limit reached (left)"

    elif x_center_normalized < 0.5 - threshold:

        if servo_position < max_pos:
            new_pos = servo_position + step
            direction = "right"

        else:
            direction = "limit reached (right)"

    else:
        # Person is centered! Snap servo to center (0)
        new_pos = 0
        direction = "centered"

    # Clamp new_pos to limits
    new_pos = max(min_pos, min(max_pos, new_pos))

    if abs(new_pos - servo_position) >= change_threshold: # If the change is significant enough
        servo_position = new_pos # Update the servo position
        servo.value = servo_position # Update the servo output

    angle = (servo_position + 1) * 90 # Map servo position to angle

    print(f"Person x: {x_center_normalized:.2f} | Servo pos: {servo_position:.2f} | Angle: {angle:.1f}° | Direction: {direction}") # Print tracking info

    return angle

if __name__ == "__main__":

    args = get_args() # Get the command-line arguments

    imx500 = IMX500(args.model) # Initialize IMX500 with model argument
    intrinsics = imx500.network_intrinsics # Get network intrinsics

    if not intrinsics: # If no intrinsics are found:
        intrinsics = NetworkIntrinsics() # Create a new instance of NetworkIntrinsics
        intrinsics.task = "object detection" # Set the task to object detection

    elif intrinsics.task != "object detection": # If the task is not object detection:
        print("Network is not an object detection task", file = sys.stderr) # Print error message
        exit()

    # Override intrinsics from args
    for key, value in vars(args).items(): # Iterate over command-line arguments

        if key == 'labels' and value is not None: # If labels file is specified:

            with open(value, 'r') as f: # Open the labels file
                intrinsics.labels = f.read().splitlines() # Read labels from file

        elif hasattr(intrinsics, key) and value is not None: # If the intrinsics has the attribute and value is not None:
            setattr(intrinsics, key, value) # Override the intrinsics attribute

    # Defaults
    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()

    intrinsics.update_with_defaults()

    if args.print_intrinsics:
        print(intrinsics)
        exit()

    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count = 12)

    imx500.show_network_fw_progress_bar()
    picam2.start(config, show_preview = True)

    if intrinsics.preserve_aspect_ratio: # If preserve_aspect_ratio is enabled
        imx500.set_auto_aspect_ratio() # Set auto aspect ratio

    last_results = None
    picam2.pre_callback = draw_detections

    while True:
        last_results = parse_detections(picam2.capture_metadata())

        person_detections = [d for d in last_results if intrinsics.labels[int(d.category)] == "person"]

        if person_detections:
            person = person_detections[0]
            x, y, w, h = person.box
            x_center = x + w / 2
            frame_width = picam2.stream_configuration("main")["size"][0]
            x_center_normalized = x_center / frame_width
            update_servo_tracking(x_center_normalized)

        else:
            print("No person detected.")
                
        obstacle_labels = {
            "chair", "couch", "bed", "bench", "table", "tv", "potted plant", 
            "car", "truck", "bottle", "vase", "wall", "refrigerator", "microwave"
        }

        obstacles = [
            d for d in last_results # Iterate over detected objects
            if intrinsics.labels[int(d.category)] in obstacle_labels # Check if the detected object is an obstacle
        ]

        for obs in obstacles: # Iterate over detected obstacles

            x, y, w, h = obs.box # Get the bounding box coordinates
            area = w * h # Calculate the area of the bounding box

            if area > 10000: # If the area is greater than 10 000
                label = intrinsics.labels[int(obs.category)] # Get the label of the detected obstacle
                print(f"Obstacle detected: {label} | Area: {area}") # Print obstacle info
                break


