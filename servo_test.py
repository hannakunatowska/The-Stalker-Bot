import argparse
import sys
from functools import lru_cache

import cv2
import numpy as np

from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics,
                                      postprocess_nanodet_detection)

# --- new imports for servo + timing ---
import time
from gpiozero import AngularServo

last_detections = []
FRAME_WIDTH = None   # will be filled from MappedArray inside draw_detections


class Detection:
    def __init__(self, coords, category, conf, metadata):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)


def parse_detections(metadata: dict):
    """Parse the output tensor into a number of detected objects, scaled to the ISP output."""
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
            postprocess_nanodet_detection(outputs=np_outputs[0], conf=threshold, iou_thres=iou,
                                          max_out_dets=max_detections)[0]
        from picamera2.devices.imx500.postprocess import scale_boxes
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
    labels = intrinsics.labels

    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    return labels


def draw_detections(request, stream="main"):
    """Draw the detections for this request onto the ISP output."""
    global FRAME_WIDTH, last_results
    detections = last_results
    labels = get_labels()
    with MappedArray(request, stream) as m:
        # record frame width once (m.array is a numpy array with shape (h, w, c))
        if FRAME_WIDTH is None:
            try:
                FRAME_WIDTH = int(m.array.shape[1])
                print("Detected FRAME_WIDTH from MappedArray:", FRAME_WIDTH)
            except Exception:
                pass

        # If there are no detection results yet, return after storing FRAME_WIDTH
        if detections is None:
            return

        for detection in detections:
            x, y, w, h = detection.box
            label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"

            # Calculate text size and position
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_x = x + 5
            text_y = y + 15

            # Create a copy of the array to draw the background with opacity
            overlay = m.array.copy()

            # Draw the background rectangle on the overlay
            cv2.rectangle(overlay,
                          (text_x, text_y - text_height),
                          (text_x + text_width, text_y + baseline),
                          (255, 255, 255),  # Background color (white)
                          cv2.FILLED)

            alpha = 0.30
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)

            # Draw text on top of the background
            cv2.putText(m.array, label, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # Draw detection box
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)

        if intrinsics.preserve_aspect_ratio:
            b_x, b_y, b_w, b_h = imx500.get_roi_scaled(request)
            color = (255, 0, 0)  # red
            cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="Path of the model",
                        default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction, help="Normalize bbox")
    parser.add_argument("--bbox-order", choices=["yx", "xy"], default="yx",
                        help="Set bbox order yx -> (y0, x0, y1, x1) xy -> (x0, y0, x1, y1)")
    parser.add_argument("--threshold", type=float, default=0.55, help="Detection threshold")
    parser.add_argument("--iou", type=float, default=0.65, help="Set iou threshold")
    parser.add_argument("--max-detections", type=int, default=10, help="Set max detections")
    parser.add_argument("--ignore-dash-labels", action=argparse.BooleanOptionalAction, help="Remove '-' labels ")
    parser.add_argument("--postprocess", choices=["", "nanodet"],
                        default=None, help="Run post process of type")
    parser.add_argument("-r", "--preserve-aspect-ratio", action=argparse.BooleanOptionalAction,
                        help="preserve the pixel aspect ratio of the input tensor")
    parser.add_argument("--labels", type=str,
                        help="Path to the labels file")
    parser.add_argument("--print-intrinsics", action="store_true",
                        help="Print JSON network_intrinsics then exit")
    return parser.parse_args()


# ---------------------------
# --- Servo helper utils ---
# ---------------------------

def clamp(v, a, b):
    return max(a, min(b, v))


def center_x_from_detections(detections, labels, target_label="person"):
    """
    Returns the center x (pixels) of the highest-confidence detection
    whose label matches target_label, and the detection bbox (x,y,w,h).
    If none found return (None, None).
    """
    if not detections:
        return None, None

    best = None
    best_conf = -1
    for d in detections:
        labelname = labels[int(d.category)] if labels is not None else None
        if labelname == target_label:
            if d.conf > best_conf:
                best_conf = d.conf
                best = d

    if best is None:
        return None, None

    x, y, w, h = best.box
    center_x = x + w / 2.0
    return center_x, (x, y, w, h)


def map_center_to_angle(center_x, frame_width, min_angle=0.0, max_angle=180.0):
    """
    Map a pixel center_x (0..frame_width) to servo angle (min_angle..max_angle).
    Returns angle in 0..180 (float) or None if center_x is None.
    """
    if center_x is None:
        return None
    frac = clamp(center_x / float(frame_width), 0.0, 1.0)
    angle = min_angle + frac * (max_angle - min_angle)
    return angle


_last_angle = None
def smooth_angle(new_angle, alpha=0.25):
    global _last_angle
    if new_angle is None:
        return None
    if _last_angle is None:
        _last_angle = new_angle
    else:
        _last_angle = _last_angle + alpha * (new_angle - _last_angle)
    return _last_angle


# ---------------------------
# --- Main program starts ---
# ---------------------------
if __name__ == "__main__":
    args = get_args()

    # This must be called before instantiation of Picamera2
    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics
    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    elif intrinsics.task != "object detection":
        print("Network is not an object detection task", file=sys.stderr)
        exit()

    # Override intrinsics from args
    for key, value in vars(args).items():
        if key == 'labels' and value is not None:
            with open(value, 'r') as f:
                intrinsics.labels = f.read().splitlines()
        elif hasattr(intrinsics, key) and value is not None:
            setattr(intrinsics, key, value)

    # Defaults
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

    # ---------------------------
    # --- Servo: gpiozero setup ---
    # ---------------------------
    # Hardware pin (BCM); change if you wire differently
    SERVO_GPIO_PIN = 17

    # AngularServo pulse range may need tuning for your servo:
    SERVO_MIN_PULSE = 0.0006   # 600 us
    SERVO_MAX_PULSE = 0.0024   # 2400 us

    # smoothing + deadzone params (tune as needed)
    SMOOTH_ALPHA = 0.20       # 0.05..0.35 typical
    DEADBAND_DEGREES = 2.0    # don't move for < 2° change

    try:
        servo = AngularServo(SERVO_GPIO_PIN, min_pulse_width=SERVO_MIN_PULSE,
                             max_pulse_width=SERVO_MAX_PULSE, initial_angle=0)
        print(f"Servo initialized on BCM pin {SERVO_GPIO_PIN}")
    except Exception as e:
        print("Failed to initialize AngularServo:", e)
        print("Make sure gpiozero is installed and you have permission to access GPIO.")
        servo = None

    last_results = None
    picam2.pre_callback = draw_detections

    last_sent_angle = None  # in 0..180 space

    try:
        while True:
            # get detection metadata (this is your existing flow)
            last_results = parse_detections(picam2.capture_metadata())

            # get labels and find person center x
            labels = get_labels()
            center_x, bbox = center_x_from_detections(last_results, labels, target_label="person")

            # if FRAME_WIDTH hasn't been discovered yet, wait a little (draw_detections will set it)
            if FRAME_WIDTH is None:
                # give draw_detections a tiny moment to run and set FRAME_WIDTH
                time.sleep(0.01)
                continue

            # map to angle 0..180
            raw_angle = map_center_to_angle(center_x, FRAME_WIDTH, min_angle=0.0, max_angle=180.0)
            smoothed = smooth_angle(raw_angle, alpha=SMOOTH_ALPHA)

            # only send to servo if big enough change
            if smoothed is not None:
                send_this = True
                if last_sent_angle is not None:
                    if abs(smoothed - last_sent_angle) < DEADBAND_DEGREES:
                        send_this = False

                if send_this and servo is not None:
                    # gpiozero.AngularServo uses -90..+90 default range, so map 0..180 -> -90..+90
                    gpiozero_angle = smoothed - 90.0
                    try:
                        servo.angle = gpiozero_angle
                        last_sent_angle = smoothed
                    except Exception as e:
                        print("Failed to move servo:", e)

                # print returned angle (0..180) so you can log/return it elsewhere
                print(f"center_x={center_x} frame_w={FRAME_WIDTH} raw={raw_angle} smoothed={smoothed} sent={last_sent_angle}")

            # tiny sleep to avoid busy-looping; tune as needed
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        # clean up servo
        try:
            if servo is not None:
                servo.detach()  # stop pulses
                servo.close()
        except Exception:
            pass

        # stop camera
        try:
            picam2.stop()
        except Exception:
            pass
