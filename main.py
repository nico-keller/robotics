import requests
import time
import cv2
import numpy as np
import math
from ultralytics import YOLO

motion_detected = False
motion_last_detected = time.time()

model = YOLO('yolov8s.pt')


def detect_objects(frame):
    results = model.predict(source=frame, imgsz=640)
    boxes = []
    for result in results[0].boxes:
        x1, y1, x2, y2 = result.xyxy[0].numpy()
        class_id = int(result.cls[0].item())
        confidence = result.conf[0].item()
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        width = int(x2 - x1)
        height = int(y2 - y1)

        boxes.append({
            "class_id": class_id,
            "confidence": confidence,
            "box": (center_x, center_y, width, height)
        })
    return boxes

def detect_motion():
    global motion_detected, motion_last_detected
    cap = cv2.VideoCapture(0)
    _, frame1 = cap.read()
    _, frame2 = cap.read()

    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        motion_detected = True
        motion_last_detected = time.time()
    else:
        motion_detected = False

    cap.release()

def check_no_motion_interval():
    detect_motion()
    if not motion_detected and (time.time() - motion_last_detected) >= 180:
        organize_items()

def set_gripper(open_value):
    payload = {"value": open_value}
    response = requests.put("https://api.interactions.ics.unisg.ch/pretendabot3/gripper", json=payload)
    if response.status_code == 200:
        print(f"Gripper set to {open_value}")
    else:
        print("Failed to set gripper.")

placement_map = {
    0: {"x": 100, "y": 200, "z": 50},  # Pen
    1: {"x": 150, "y": 250, "z": 50},  # Notebook
}

def decide_placement(item):
    return placement_map.get(item["class_id"], {"x": 200, "y": 300, "z": 50})

def get_current_objects():
    cap = cv2.VideoCapture(1)
    ret, frame = cap.read()
    if not ret:
        return None
    boxes = detect_objects(frame)
    cap.release()
    return boxes

def cartesian_to_polar(x, y, z):
    r = math.sqrt(x ** 2 + y ** 2)
    theta = math.degrees(math.atan2(y, x))
    return {"radius": r, "angle": theta, "height": z}


transformation_matrix = np.array([[0.1, 0, 0], [0, 0.1, 0], [0, 0, 1]])

def pixel_to_real(x_pixel, y_pixel):
    pixel_coords = np.array([x_pixel, y_pixel, 1])
    real_coords = np.dot(transformation_matrix, pixel_coords)
    return {"x": real_coords[0] / real_coords[2], "y": real_coords[1] / real_coords[2], "z": 50}



def initialize_robot():
    response = requests.put("https://api.interactions.ics.unisg.ch/pretendabot3/initialize")
    if response.status_code == 202:
        print("Robot initialized to original state.")
    else:
        print("Failed to initialize the robot.")


def move_to_target(cartesian_position, target_rotation, speed=50):
    polar_position = cartesian_to_polar(cartesian_position["x"], cartesian_position["y"], cartesian_position["z"])
    payload = {
        "target": {
            "polar_coordinate": {
                "radius": polar_position["radius"],
                "angle": polar_position["angle"],
                "height": polar_position["height"]
            },
            "rotation": target_rotation
        },
        "speed": speed
    }
    response = requests.put("https://api.interactions.ics.unisg.ch/pretendabot3/tcp/target", json=payload)
    if response.status_code == 200:
        print(f"Moving to target in polar coordinates: {polar_position} at speed {speed}")
    else:
        print("Failed to set target position.")


def organize_items():
    initialize_robot()
    objects = get_current_objects()
    if not objects:
        print("No objects detected.")
        return
    for obj in objects:
        x_pixel, y_pixel, _, _ = obj["box"]
        obj_position = pixel_to_real(x_pixel, y_pixel)
        polar_position = cartesian_to_polar(obj_position["x"], obj_position["y"], obj_position["z"])
        target_rotation = {"roll": 180, "pitch": 0, "yaw": 0}
        move_to_target(polar_position, target_rotation)
        set_gripper(0)
        target_position = decide_placement(obj)
        target_polar_position = cartesian_to_polar(target_position["x"], target_position["y"], target_position["z"])
        move_to_target(target_polar_position, target_rotation)
        set_gripper(20)


def main():
    while True:
        check_no_motion_interval()
        time.sleep(5)


main()
