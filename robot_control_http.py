import requests
import time
import numpy as np


# class for robot controls
class robot():
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

    # carthesian to polar conversion
    def cart2pol(self, x, y):
        rho = np.sqrt(x ** 2 + y ** 2)
        phi = np.arctan2(y, x)
        print(rho, phi)
        return (rho, phi)

    # polar to carthesian conversion
    def pol2cart(self, rho, phi):
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        return (x, y)

    def move(self, x_target, y_target):
        url = self.BASE_URL + self.MOVE
        rho, phi = self.cart2pol(x_target, y_target)
        x_new, y_new = self.pol2cart(rho, phi)
        new_pos = {"target": {"coordinate": {"x": x_new, "y": y_new},
                              "rotation": {"roll": self.roll, "pitch": self.pitch, "yaw": self.yaw}}, "speed": 50}
        response = requests.put(url, json=new_pos, headers={"Authentication": self.TOKEN})
        time.sleep(1)
        if response.status_code == 200:
            print(
                f"Successfully moved the robot to polar coordinates: radius={rho:.2f}, angle={np.degrees(phi):.2f}")            # update positions
            self.data()
        else:
            print("Failed to move the robot. Status code:", response.status_code)

    # rotate goes here
    def rotate(self, angle):
        url = self.BASE_URL + self.ROTATE
        # compute angle change compared to origin
        self.angleChange += angle
        angle1 = angle % 360
        # Convert angle to radians
        angle2 = np.radians(angle1)
        # Compute sine and cosine of angle
        sin_angle = np.sin(angle2)
        cos_angle = np.cos(angle2)
        # Compute rotated point coordinates
        x_new = self.x * cos_angle - self.y * sin_angle
        y_new = self.x * sin_angle + self.y * cos_angle
        # if setting robot back to origin: set the new y to 0 (otherwise is value close to zero)
        if self.angleChange == 0:
            y_new = 0
        yaw_new = self.yaw + angle
        new_pos = {"target": {"coordinate": {"x": x_new, "y": y_new, "z": self.z},
                              "rotation": {"roll": self.roll, "pitch": self.pitch, "yaw": yaw_new}}, "speed": 50}
        time.sleep(1)
        response = requests.put(url, json=new_pos, headers={"Authentication": self.TOKEN})
        if response.status_code == 200:
            print("Successfully rotated the robot", angle, "degrees!")
            # update positions
            self.data()
        else:
            print("Failed to rotate the robot. Status code:", response.status_code)

    def toggle(self):
        url = self.BASE_URL + self.TOGGLE
        cur = (requests.get(url, headers={"Authentication": self.TOKEN}))
        # if the gripper is closed, open, otherwise close it
        if cur.json() == 0:
            new_gripper = 100
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

    def main(self):
        while True:
            command = input("Command: ")
            parts = command.split()
            if len(parts) == 3:
                command_name, x, y = parts
                if command_name == "move":
                    try:
                        # Convert x, y, z to float and call move with these parameters
                        x = float(x)
                        y = float(y)
                        self.move(x, y)
                    except ValueError:
                        print("Invalid coordinates. Please enter numeric values for x, y.")
                else:
                    print("Invalid command. Use `move x y` for Cartesian movement.")
            elif len(parts) == 2:
                command_name, param = parts
                if command_name == "rotate":
                    try:
                        angle = int(param)
                        self.rotate(angle)
                    except ValueError:
                        print("Invalid angle. Please enter an integer value.")
                else:
                    print("Invalid command. Use `rotate angle` to rotate the robot.")
            elif len(parts) == 1:
                command_name = parts[0]
                if command_name == "connect":
                    self.connect()
                elif command_name == "toggle":
                    self.toggle()
                elif command_name == "log_off":
                    self.log_off()
                    break
                else:
                    print("Invalid command")
            else:
                print("Invalid command")
            time.sleep(1)  # wait for 1 second before processing the next command


# create robot instance and run main()
robo = robot()
robo.main()