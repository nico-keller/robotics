import requests
import time
import cv2
from ultralytics import YOLO
import numpy as np

# class for robot controls
class Robot:
    def __init__(self):
        self.BASE_URL = "https://api.interactions.ics.unisg.ch/cherrybot2"
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
        self.model = YOLO("yolov8x.pt")

    def _request(self, method, endpoint, data=None):
        url = self.BASE_URL + endpoint
        headers = {"Authentication": self.TOKEN} if self.TOKEN else {}
        response = requests.request(method, url, json=data, headers=headers)
        return response

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
            # print robot coordinates
            print(self.x, self.y, self.z, self.roll, self.pitch, self.yaw)
        else:
            print("Failed to connect to the robot. Status code:", response.status_code)

    def connect(self):
        url = self.BASE_URL + self.CONNECT
        user = {"name": "test", "email": "test@student.unisg.ch"}
        response = requests.post(url, json=user)
        if response.status_code == 200:
            time.sleep(1)
            # get token
            self.TOKEN = ((requests.get(url)).json())["token"]
            print("Successfully connected to the robot!")
            # update positions
            self.data()
            time.sleep(1)
        else:
            print("Failed to connect to the robot. Status code:", response.status_code)

    def toggle(self):
        url = self.BASE_URL + self.TOGGLE
        cur = (requests.get(url, headers={"Authentication": self.TOKEN}))
        # if the gripper is closed, open, otherwise close it
        if cur.json() == 0:
            new_gripper = 200
        else:
            new_gripper = 0
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

    def move_to_position(self, x, y, z, roll=180, pitch=0, yaw=0, speed=125):
        target = {
            "target": {
                "coordinate": {"x": x, "y": y, "z": z},
                "rotation": {"roll": roll, "pitch": pitch, "yaw": yaw},
            },
            "speed": speed,
        }
        response = self._request("PUT", self.MOVE, target)
        if response.status_code == 200:
            print(f"Successfully moved the robot to position: ({x}, {y}, {z})")
        else:
            print("Failed to move the robot. Status code:", response.status_code)

    def grab_and_drop(self, drop_position):
        self.move_to_position(400, 0, 300)  # Move to grab position
        time.sleep(2)
        self.move_to_position(400, 0, 15)  # Lower to grab
        time.sleep(3)
        self.toggle()  # Grab item
        time.sleep(3)
        self.move_to_position(400, 0, 300)  # Lift item
        time.sleep(2)
        self.move_to_position(*drop_position)  # Move to drop position
        time.sleep(3)
        self.toggle()  # Drop item

    def operator(self):
        url = self.BASE_URL + self.CONNECT
        response = requests.get(url)
        if response.status_code == 200:
            response_data = response.json()
            print("Robot is currently operated by:", response_data)
        elif response.status_code == 204:
            print("Nobody is currently operating the robot.")
        else:
            print("ERROR: Invalid response")

    def initialize(self):
        if not self.TOKEN:
            print("ERROR: Token not found. Please connect to the robot first.")
            return
        url = f"{self.BASE_URL}/initialize"
        response = requests.put(url, headers={"Authentication": self.TOKEN})
        if response.status_code in [200, 202]:
            print("Successfully initialized robot's position.")
            self.data()
        else:
            print("Failed to initialize robot's position. Status code:", response.status_code)

    def sort_recycling_materials(self, stream_url):
        """
        Detects and sorts recycling materials using the video stream.
        Moves detected materials to their respective locations.
        """
        webcam = cv2.VideoCapture(stream_url)
        if not webcam.isOpened():
            print("Error: Unable to open video stream.")
            return

        while True:
            ret, frame = webcam.read()
            if not ret:
                print("Stream disconnected or unavailable.")
                break

            # Define a fixed central region for detection
            height, width, _ = frame.shape
            center_x, center_y = width // 2, height // 2
            region_width, region_height = int(width // 8), int(height // 8 * 1.5)
            x1, y1 = max(center_x - region_width // 2, 0), max(center_y - region_height // 2, 0)
            x2, y2 = min(center_x + region_width // 2, width), min(center_y + region_height // 2, height)
            central_region = frame[y1:y2, x1:x2]

            # YOLO detection
            results = self.model(central_region, conf=0.5)
            detected_materials = [
                self.model.names[int(box.cls.item())] for result in results for box in result.boxes
            ]

            if detected_materials:
                material = detected_materials[0]  # Use the first detected material
                print(f"Detected Material: {material}")

                # Perform sorting based on material
                if material == "plastic":
                    print("Sorting plastic to the left...")
                    self.grab_and_drop((400, 200, 300))
                elif material == "metal":
                    print("Sorting metal to the right...")
                    self.grab_and_drop((400, -200, 300))
                elif material == "glass":
                    print("Sorting glass forward...")
                    self.grab_and_drop((500, 0, 300))
                else:
                    print(f"Unknown material detected: {material}")
            else:
                print("No materials detected.")

        webcam.release()

# move to the left
# grab_and_drop((400, 200, 300))

# move to the right
# grab_and_drop((400, -200, 300))

# move forward
# grab_and_drop((500, 0, 300))


