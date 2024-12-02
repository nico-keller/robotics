import requests
import time
import cv2
from ultralytics import YOLO

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
        self.model = YOLO("recycling.pt")

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
            #self.toggle()
            time.sleep(1)
        else:
            print("Failed to connect to the robot. Status code:", response.status_code)

    def toggle(self):
        url = self.BASE_URL + self.TOGGLE
        cur = (requests.get(url, headers={"Authentication": self.TOKEN}))
        # if the gripper is closed, open, otherwise close it
        if cur.json() == 100:
            new_gripper = 800
        else:
            new_gripper = 100
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
        self.move_to_position(400, 0, 2)  # Lower to grab
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
        webcam = cv2.VideoCapture(stream_url)
        if not webcam.isOpened():
            print("Error: Unable to open video stream.")
            return

        try:
            while True:
                for _ in range(5):
                    webcam.read()

                ret, frame = webcam.read()
                if not ret:
                    print("Stream disconnected or unavailable.")
                    break

                height, width, _ = frame.shape
                center_x, center_y = width // 2, height // 2
                region_width, region_height = int(width // 6), int(height // 6)
                shift_x, shift_y = 35, 10

                x1 = center_x - region_width // 2 - shift_x
                y1 = center_y - region_height // 2 - shift_y
                x2 = center_x + region_width // 2 - shift_x
                y2 = center_y + region_height // 2 - shift_y

                x1, y1 = max(x1, 0), max(y1, 0)
                x2, y2 = min(x2, width), min(y2, height)

                detected_materials = []
                for _ in range(3):  # Check 3 consecutive frames
                    ret, verify_frame = webcam.read()
                    if not ret:
                        break
                    
                    detection_region = verify_frame[y1:y2, x1:x2]
                    results = self.model(detection_region, conf=0.5)
                    
                    frame_materials = []
                    for result in results:
                        for box in result.boxes:
                            if float(box.conf.item()) >= 0.5:
                                frame_materials.append(self.model.names[int(box.cls.item())])
                    
                    if frame_materials:
                        detected_materials.append(frame_materials[0])
                    
                    time.sleep(0.1)

                if len(detected_materials) >= 2 and len(set(detected_materials)) == 1:
                    material = detected_materials[0]
                    print(f"Verified Material Detection: {material}")

                    webcam.release()
                    cv2.destroyAllWindows()

                    if material == "glass":
                        print("Sorting glass to the left...")
                        self.grab_and_drop((400, 200, 300))
                    elif material == "metal":
                        print("Sorting metal to the right...")
                        self.grab_and_drop((400, -200, 300))
                    elif material == "plastic":
                        print("Sorting plastic forward...")
                        self.grab_and_drop((500, 0, 300))
                    else:
                        print(f"Unknown material detected: {material}")

                    time.sleep(3)

                    webcam = cv2.VideoCapture(stream_url)
                    if not webcam.isOpened():
                        print("Error: Unable to reopen video stream.")
                        break
                    
                    for _ in range(5):
                        webcam.read()

                time.sleep(0.2)

        finally:
            webcam.release()
            cv2.destroyAllWindows()

# move to the left
# grab_and_drop((400, 200, 300))

# move to the right
# grab_and_drop((400, -200, 300))

# move forward
# grab_and_drop((500, 0, 300))


