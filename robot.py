import requests
import time
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

    def main(self):
        while True:
            print("\nPlease select an option:")
            print("1. Connect")
            print("2. logoff")
            print("3. initialize")
            print("4. Toggle the gripper")
            print("5. left")
            print("6. right")

            choice = input("Enter your choice (1-11): ")
            if choice == '1':
                self.connect()
            elif choice == '2':
                self.initialize()
                self.log_off()
                break
            elif choice == '3':
                self.initialize()
            elif choice == '4':
                self.toggle()
            elif choice == "5":
                self.grab_and_drop((400, 500, 300))  # Left drop position
            elif choice == "6":
                self.grab_and_drop((400, -500, 300))  # Right drop position
            else:
                print("Invalid choice. Please select a valid option.")
            time.sleep(1)  # Wait for 1 second before processing the next command

# create robot instance and run main()
robo = Robot()
robo.main()




