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

# --- Setup ---

servo = Servo(18, min_pulse_width=0.5 / 1000, max_pulse_width=2.5 / 1000)
servo_position = 0.0
servo.value = servo_position


class Detection:
    """Represents a single object detection."""

    def __init__(self, coords, category, conf, metadata):
        """Creates a Detection object recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)


def parse_detections(metadata: dict):
    """Parse the output tensor into detected objects."""
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
        boxes, scores, classes = postprocess_nanodet_detection(
            outputs=np_outputs[0], conf=threshold, iou_thres=iou, max_out_dets=max_detections
        )[0]
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


@lru_cache
def get_labels():
    """Gets the labels for the model."""
    labels = intrinsics.labels
    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    return labels


def draw_detections(request, stream="main"):
    """Draws the detections for this request onto the ISP output."""
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
            cv2.rectangle(overlay, (text_x, text_y - text_height),
                          (text_x + text_width, text_y + baseline), (255, 255, 255), cv2.FILLED)
            alpha = 0.30
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)
            cv2.putText(m.array, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)

        if intrinsics.preserve_aspect_ratio:
            b_x, b_y, b_w, b_h = imx500.get_roi_scaled(request)
            color = (255, 0, 0)
            cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))


def get_args():
    """Gets command line arguments for the script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
    parser.add_argument("--fps", type=int)
    parser.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction)
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


def update_servo_tracking(x_center_normalized):
    """Updates servo tracking and returns servo angle + direction string."""
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
        new_pos = 0
        direction = "centered"

    new_pos = max(min_pos, min(max_pos, new_pos))
    if abs(new_pos - servo_position) >= change_threshold:
        servo_position = new_pos
        servo.value = servo_position

    angle = (servo_position + 1) * 90
    print(f"Person x: {x_center_normalized:.2f} | Servo pos: {servo_position:.2f} | Angle: {angle:.1f}° | Direction: {direction}")
    return angle, direction


def get_tracking_data():
    """
    Captures detections, tracks the person, checks for obstacles,
    and returns (angle, direction, obstacle, person_height_normalized)
    """
    last_results = parse_detections(picam2.capture_metadata())

    # --- Find person ---
    person_detections = [d for d in last_results if intrinsics.labels[int(d.category)] == "person"]
    person_height_norm = None
    angle, direction = 90, "none"

    if person_detections:
        person = person_detections[0]
        x, y, w, h = person.box
        x_center = x + w / 2
        frame_width, frame_height = picam2.stream_configuration("main")["size"]
        x_center_normalized = x_center / frame_width
        person_height_norm = h / frame_height  # <--- NEW: normalized height
        angle, direction = update_servo_tracking(x_center_normalized)
    else:
        print("No person detected.")

    # --- Detect obstacles ---
    obstacle_labels = {
        "chair", "couch", "bed", "bench", "table", "tv", "potted plant",
        "car", "truck", "bottle", "vase", "wall", "refrigerator", "microwave"
    }
    obstacle_detected = False
    for obs in last_results:
        if intrinsics.labels[int(obs.category)] in obstacle_labels:
            x, y, w, h = obs.box
            if w * h > 10000:
                label = intrinsics.labels[int(obs.category)]
                print(f"Obstacle detected: {label}")
                obstacle_detected = True
                break

    return angle, direction, obstacle_detected, person_height_norm


# --- Camera Initialization (as before) ---
args = get_args()
imx500 = IMX500(args.model)
intrinsics = imx500.network_intrinsics or NetworkIntrinsics()
if not intrinsics.task:
    intrinsics.task = "object detection"
picam2 = Picamera2(imx500.camera_num)
config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12)
picam2.start(config, show_preview=True)

if __name__ == "__main__":
    print("Starting standalone camera-servo tracking test...")
    try:
        while True:
            angle, direction, obstacle, person_height = get_tracking_data()

            if person_height:
                print(f"→ Person height (normalized): {person_height:.2f}")
            if obstacle:
                print("⚠️ Obstacle detected!")
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("Stopped by user.")
        picam2.stop()

