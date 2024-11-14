import requests
import time
import cv2
import numpy as np
import math
from ultralytics import YOLO

# Robot class for control and manipulation
class Robot():
    def __init__(self):
        self.BASE_URL = "https://api.interactions.ics.unisg.ch/pretendabot4"
        self.CONNECT = "/operator"
        self.MOVE = "/tcp/target"
        self.ROTATE = "/tcp/target"
        self.TOGGLE = "/gripper"
        self.TOKEN = ""
        self.LOG_OFF = "/operator/"
        self.gripper_default = None
        self.x = None
        self.y = None
        self.z = None
        self.roll = None
        self.pitch = None
        self.yaw = None
        self.angleChange = 0

    def data(self):
        url = self.BASE_URL + "/tcp"
        time.sleep(1)
        response = (requests.get(url, headers={"Authentication": self.TOKEN}))
        if response.status_code == 200:
            time.sleep(1)
            self.x = (response.json())["coordinate"]["x"]
            self.y = (response.json())["coordinate"]['y']
            self.z = (response.json())["coordinate"]['z']
            self.roll = (response.json())["rotation"]['roll']
            self.pitch = (response.json())["rotation"]['pitch']
            self.yaw = (response.json())["rotation"]['yaw']
            print("Current Position:", self.x, self.y, self.z, self.roll, self.pitch, self.yaw)
        else:
            print("Failed to connect to the robot. Status code:", response.status_code)

    def connect(self):
        url = self.BASE_URL + self.CONNECT
        user = {"name": "test", "email": "test@student.unisg.ch"}
        response = requests.post(url, json=user)
        if response.status_code == 200:
            time.sleep(1)
            self.TOKEN = ((requests.get(url)).json())["token"]
            print("Successfully connected to the robot!")
            self.data()
            time.sleep(1)
        else:
            print("Failed to connect to the robot. Status code:", response.status_code)

    def cart2pol(self, x, y):
        rho = np.sqrt(x ** 2 + y ** 2)
        phi = np.arctan2(y, x)
        return (rho, phi)

    def pol2cart(self, rho, phi):
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        return (x, y)

    def move(self, distance):
        url = self.BASE_URL + self.MOVE
        rho, phi = self.cart2pol(self.x, self.y)
        x_new, y_new = self.pol2cart(rho + distance, phi)
        new_pos = {"target": {"coordinate": {"x": x_new, "y": y_new, "z": self.z},
                              "rotation": {"roll": self.roll, "pitch": self.pitch, "yaw": self.yaw}}, "speed": 50}
        response = requests.put(url, json=new_pos, headers={"Authentication": self.TOKEN})
        time.sleep(1)
        if response.status_code == 200:
            print("Successfully moved the robot", distance, "units!")
            self.data()
        else:
            print("Failed to move the robot. Status code:", response.status_code)

    def rotate(self, angle):
        url = self.BASE_URL + self.ROTATE
        self.angleChange += angle
        angle1 = angle % 360
        angle2 = np.radians(angle1)
        sin_angle = np.sin(angle2)
        cos_angle = np.cos(angle2)
        x_new = self.x * cos_angle - self.y * sin_angle
        y_new = self.x * sin_angle + self.y * cos_angle
        if self.angleChange == 0:
            y_new = 0
        yaw_new = self.yaw + angle
        new_pos = {"target": {"coordinate": {"x": x_new, "y": y_new, "z": self.z},
                              "rotation": {"roll": self.roll, "pitch": self.pitch, "yaw": yaw_new}}, "speed": 50}
        time.sleep(1)
        response = requests.put(url, json=new_pos, headers={"Authentication": self.TOKEN})
        if response.status_code == 200:
            print("Successfully rotated the robot", angle, "degrees!")
            self.data()
        else:
            print("Failed to rotate the robot. Status code:", response.status_code)

    def toggle(self):
        url = self.BASE_URL + self.TOGGLE
        cur = (requests.get(url, headers={"Authentication": self.TOKEN}))
        new_gripper = 100 if cur.json() == 0 else 0
        time.sleep(1)
        response = requests.put(url, json=new_gripper, headers={"Authentication": self.TOKEN})
        if response.status_code == 200:
            print("Successfully toggled the gripper!")
        else:
            print("Failed to toggle the gripper. Status code:", response.status_code)

    def log_off(self):
        url = self.BASE_URL + self.LOG_OFF + self.TOKEN
        requests.put(self.BASE_URL + "/initialize", headers={"Authentication": self.TOKEN})
        time.sleep(1)
        response = requests.delete(url)
        if response.status_code == 200:
            print("Successfully logged off from the robot!")
        else:
            print("Failed to log off from the robot. Status code:", response.status_code)


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
        boxes.append({"class_id": class_id, "confidence": confidence, "box": (center_x, center_y, width, height)})
    return boxes

transformation_matrix = np.array([[0.1, 0, 0], [0, 0.1, 0], [0, 0, 1]])

def pixel_to_real(x_pixel, y_pixel):
    pixel_coords = np.array([x_pixel, y_pixel, 1])
    real_coords = np.dot(transformation_matrix, pixel_coords)

    x_real = real_coords[0] / real_coords[2]
    y_real = real_coords[1] / real_coords[2]
    z_real = 50

    return x_real, y_real, z_real


def calculate_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance


# Dictionary mapping class IDs to specific target coordinates for organization
placement_map = {
    0: {"x": 100, "y": 200, "z": 50},  # Example position for class ID 0, e.g., 'pen'
    1: {"x": 150, "y": 250, "z": 50},  # Example position for class ID 1, e.g., 'notebook'
    # Add additional items here as needed
}


def decide_placement(obj):
    class_id = obj["class_id"]

    target_position = placement_map.get(class_id, {"x": 200, "y": 300, "z": 50})
    return target_position


def main_loop(robo):
    robo.connect()

    last_activity = time.time()

    while True:
        ret, frame = cv2.VideoCapture(0).read()
        if not ret:
            break

        objects = detect_objects(frame)

        for obj in objects:
            x, y, z = obj['box'][0], obj['box'][1], 50
            robo.move(distance=10)
            robo.rotate(angle=30)
            robo.toggle()

        if time.time() - last_activity > 180:
            print("No activity detected, organizing...")

            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                objects = detect_objects(frame)
            else:
                print("Error: Unable to capture frame for object detection.")
                objects = []
            cap.release()

            for obj in objects:
                x_pixel, y_pixel, _, _ = obj["box"]
                x_cartesian, y_cartesian, z_cartesian = pixel_to_real(x_pixel,
                                                                      y_pixel)

                # Move robot to object's location and pick it up
                robo.move(distance=10)
                robo.toggle()

                target_position = decide_placement(obj)
                target_distance = calculate_distance(robo.x, robo.y, target_position["x"],
                                                     target_position["y"])
                robo.move(target_distance)
                robo.toggle()

            last_activity = time.time()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    robo.log_off()


robo = Robot()
main_loop(robo)
