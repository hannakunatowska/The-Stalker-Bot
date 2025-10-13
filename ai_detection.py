# --- Imports ---

import argparse
import sys
from functools import lru_cache
import cv2
import numpy as np

from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection
from picamera2.devices.imx500.postprocess import scale_boxes

from gpiozero import Servo
import time

# --- Definitions ---

last_detections = []
last_angle = 90           # Default servo angle
last_direction = "centered"
last_obstacle = False     # Whether an obstacle is detected

# --- Setup ---

servo = Servo(18, min_pulse_width = 0.5 / 1000, max_pulse_width = 2.5 / 1000)
servo_position = 0.0
servo.value = servo_position

# --- Detection Class ---

class Detection:
    """Represents a single object detection."""
    def __init__(self, coords, category, conf, metadata):
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)

# --- Detection Parsing ---

def parse_detections(metadata: dict):
    """Parse the output tensor into detections."""
    global last_detections

    bbox_normalization = intrinsics.bbox_normalization
    bbox_order = intrinsics.bbox_order
    threshold = args.threshold
    iou = args.iou
    max_detections = args.max_detections

    np_outputs = imx500.get_outputs(metadata, add_batch=True)
    input_w, input_h = imx500.get_input_size()

    if np_outputs is None:
        return last_detections

    if intrinsics.postprocess == "nanodet":
        boxes, scores, classes = \
            postprocess_nanodet_detection(outputs=np_outputs[0], conf=threshold, iou_thres=iou, max_out_dets=max_detections)[0]
        boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
    else:
        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
        if bbox_normalization:
            boxes = boxes / input_h
        if bbox_order == "xy":
            boxes = boxes[:, [1, 0, 3, 2]]
        boxes = np.array_split(boxes, 4, axis=1)
        boxes = zip(*boxes)

    last_detections = [
        Detection(box, category, score, metadata)
        for box, score, category in zip(boxes, scores, classes)
        if score > threshold
    ]
    return last_detections

# --- Label Handling ---

@lru_cache
def get_labels():
    """Gets labels for the model."""
    labels = intrinsics.labels
    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    return labels

# --- Drawing Function ---

def draw_detections(request, stream="main"):
    """Draws the detections on the video stream."""
    detections = last_results
    if detections is None:
        return
    labels = get_labels()
    with MappedArray(request, stream) as m:
        for detection in detections:
            x, y, w, h = detection.box
            label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_x = x + 5
            text_y = y + 15
            overlay = m.array.copy()
            cv2.rectangle(overlay, (text_x, text_y - text_height), (text_x + text_width, text_y + baseline), (255, 255, 255), cv2.FILLED)
            alpha = 0.30
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)
            cv2.putText(m.array, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)
        if intrinsics.preserve_aspect_ratio:
            b_x, b_y, b_w, b_h = imx500.get_roi_scaled(request)
            color = (255, 0, 0)
            cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))

# --- Argument Parsing ---

def get_args():
    """Gets command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="Path of the model", default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction, help="Normalize bbox")
    parser.add_argument("--bbox-order", choices=["yx", "xy"], default="yx")
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument("--iou", type=float, default=0.65)
    parser.add_argument("--max-detections", type=int, default=10)
    parser.add_argument("--ignore-dash-labels", action=argparse.BooleanOptionalAction)
    parser.add_argument("--postprocess", choices=["", "nanodet"], default=None)
    parser.add_argument("-r", "--preserve-aspect-ratio", action=argparse.BooleanOptionalAction)
    parser.add_argument("--labels", type=str)
    parser.add_argument("--print-intrinsics", action="store_true")
    return parser.parse_args()

# --- Servo Tracking ---

def update_servo_tracking(x_center_normalized):
    """Updates servo based on normalized x center position."""
    global servo_position, last_angle, last_direction

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
        new_pos = 0
        direction = "centered"

    new_pos = max(min_pos, min(max_pos, new_pos))
    if abs(new_pos - servo_position) >= change_threshold:
        servo_position = new_pos
        servo.value = servo_position

    angle = (servo_position + 1) * 90
    last_angle = angle
    last_direction = direction

    print(f"Person x: {x_center_normalized:.2f} | Servo pos: {servo_position:.2f} | Angle: {angle:.1f}° | Direction: {direction}")
    return angle

# --- NEW FUNCTION ADDED HERE ---

def get_tracking_data():
    """
    Returns the current servo and obstacle tracking data.

    Returns:
        tuple: (angle, direction, obstacle)
            angle (float): Servo angle in degrees.
            direction (str): "left", "right", "centered", or "limit reached".
            obstacle (bool): True if an obstacle is detected.
    """
    return last_angle, last_direction, last_obstacle, person_height_norm

# --- Main Execution Block ---

if __name__ == "__main__":

    args = get_args()
    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics

    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    elif intrinsics.task != "object detection":
        print("Network is not an object detection task", file=sys.stderr)
        exit()

    for key, value in vars(args).items():
        if key == 'labels' and value is not None:
            with open(value, 'r') as f:
                intrinsics.labels = f.read().splitlines()
        elif hasattr(intrinsics, key) and value is not None:
            setattr(intrinsics, key, value)

    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()

    intrinsics.update_with_defaults()
    if args.print_intrinsics:
        print(intrinsics)
        exit()

    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12)
    imx500.show_network_fw_progress_bar()
    picam2.start(config, show_preview=True)

    if intrinsics.preserve_aspect_ratio:
        imx500.set_auto_aspect_ratio()

    last_results = None
    picam2.pre_callback = draw_detections

    while True:
        last_results = parse_detections(picam2.capture_metadata())

        person_detections = [d for d in last_results if intrinsics.labels[int(d.category)] == "person"]
        person_height_norm = None

        if person_detections:
            person = person_detections[0]
            x, y, w, h = person.box
            x_center = x + w / 2
            frame_width = picam2.stream_configuration("main")["size"][0]
            x_center_normalized = x_center / frame_width
            person_height_norm = h / frame_height  # <--- NEW: normalized height
            update_servo_tracking(x_center_normalized)
        else:
            print("No person detected.")

        # --- Obstacle detection section ---
        obstacle_labels = {
            "chair", "couch", "bed", "bench", "table", "tv", "potted plant",
            "car", "truck", "bottle", "vase", "wall", "refrigerator", "microwave"
        }

        obstacles = [
            d for d in last_results
            if intrinsics.labels[int(d.category)] in obstacle_labels
        ]

        # Update global obstacle state
        global last_obstacle
        last_obstacle = False
        for obs in obstacles:
            x, y, w, h = obs.box
            area = w * h
            if area > 10000:
                label = intrinsics.labels[int(obs.category)]
                print(f"Obstacle detected: {label} | Area: {area}")
                last_obstacle = True
                break
