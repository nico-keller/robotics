import requests
import time
import numpy as np

# idea
# 1. go down to grab coordinate
# 2. close gripper
# 3. go up
# 4. go to specific location --> has to recognize if piece of clothing has color
# 5. open gripper for dropping clothes
# 6. go back to center position
# 7. repeat

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

    def move_to_grab_position(self):
        url = self.BASE_URL + self.MOVE

        # Include the current z coordinate in the new position
        target = {
            "target": {
                "coordinate": {
                    "x": 400,
                    "y": 0,
                    "z": 300
                },
                "rotation": {
                    "roll": 180,
                    "pitch": 0,
                    "yaw": 0
                }
            },
            "speed": 125
        }

        response = requests.put(url, json=target, headers={"Authentication": self.TOKEN})
        time.sleep(1)
        if response.status_code == 200:
            print(
                f"Successfully moved the robot")
            # update positions
            self.data()
        else:
            print("Failed to move the robot. Status code:", response.status_code)

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

    def grab_and_drop_left(self):
        self.move_to_grab_position()
        time.sleep(2)
        self.lower_for_grab()
        time.sleep(1)
        self.toggle()
        time.sleep(2)
        self.lift_object()
        time.sleep(1)
        self.move_to_drop_position_left()
        time.sleep(2)
        self.toggle()
        print("Grab and drop completed.")


    def grab_and_drop_right(self):
        self.move_to_grab_position()
        time.sleep(2)
        self.lower_for_grab()
        time.sleep(2)
        self.toggle()
        time.sleep(2)
        self.lift_object()
        time.sleep(2)
        self.move_to_drop_position_right()
        time.sleep(1)
        self.toggle()
        print("Grab and drop completed.")

    def lower_for_grab(self):
        url = self.BASE_URL + self.MOVE

        # Include the current z coordinate in the new position
        target = {
            "target": {
                "coordinate": {
                    "x": 400,
                    "y": 0,
                    "z": 15
                },
                "rotation": {
                    "roll": 180,
                    "pitch": 0,
                    "yaw": 0
                }
            },
            "speed": 125
        }

        response = requests.put(url, json=target, headers={"Authentication": self.TOKEN})
        time.sleep(1)
        if response.status_code == 200:
            print(
                f"Successfully moved the robot")
            # update positions
            self.data()
        else:
            print("Failed to move the robot. Status code:", response.status_code)

    def lift_object(self):
        url = self.BASE_URL + self.MOVE

        # Include the current z coordinate in the new position
        target = {
            "target": {
                "coordinate": {
                    "x": 400,
                    "y": 0,
                    "z": 200
                },
                "rotation": {
                    "roll": 180,
                    "pitch": 0,
                    "yaw": 0
                }
            },
            "speed": 125
        }

        response = requests.put(url, json=target, headers={"Authentication": self.TOKEN})
        time.sleep(1)
        if response.status_code == 200:
            print(
                f"Successfully moved the robot")
            # update positions
            self.data()
        else:
            print("Failed to move the robot. Status code:", response.status_code)

    def move_to_drop_position_left(self):
        url = self.BASE_URL + self.MOVE

        # Include the current z coordinate in the new position
        target = {
            "target": {
                "coordinate": {
                    "x": 400,
                    "y": 400,
                    "z": 200
                },
                "rotation": {
                    "roll": 180,
                    "pitch": 0,
                    "yaw": 0
                }
            },
            "speed": 125
        }

        response = requests.put(url, json=target, headers={"Authentication": self.TOKEN})
        time.sleep(1)
        if response.status_code == 200:
            print(
                f"Successfully moved the robot")
            # update positions
            self.data()
        else:
            print("Failed to move the robot. Status code:", response.status_code)


    def move_to_drop_position_right(self):
        url = self.BASE_URL + self.MOVE

        # Include the current z coordinate in the new position
        target = {
            "target": {
                "coordinate": {
                    "x": 400,
                    "y": -400,
                    "z": 200
                },
                "rotation": {
                    "roll": 180,
                    "pitch": 0,
                    "yaw": 0
                }
            },
            "speed": 125
        }

        response = requests.put(url, json=target, headers={"Authentication": self.TOKEN})
        time.sleep(1)
        if response.status_code == 200:
            print(
                f"Successfully moved the robot")
            # update positions
            self.data()
        else:
            print("Failed to move the robot. Status code:", response.status_code)

    def main(self):
        while True:
            print("\nPlease select an option:")
            print("1. Connect")
            print("2. logoff")
            print("3. initialize")
            print("4. Toggle the gripper")
            print("5. move to grab position")
            print("6. lower forgrab")
            print("7. lift")
            print("8. move to drop position left")
            print("9. move to drop position right")
            print("10. Complete drag and drop left")
            print("11. Complete drag and drop right")

            choice = input("Enter your choice (1-11): ")
            if choice == '1':
                self.connect()
            elif choice == '2':
                self.log_off()
                break
            elif choice == '3':
                self.initialize()
            elif choice == '4':
                self.toggle()
            elif choice == '5':
                self.move_to_grab_position()
            elif choice == '6':
                self.lower_for_grab()
            elif choice == '7':
                self.lift_object()
            elif choice == '8':
                self.move_to_drop_position_left()
            elif choice == '9':
                self.move_to_drop_position_right()
            elif choice == '10':
                self.grab_and_drop_left()
            elif choice == '11':
                self.grab_and_drop_right()
            else:
                print("Invalid choice. Please select a number between 1 and 8.")
            time.sleep(1)  # Wait for 1 second before processing the next command

# create robot instance and run main()
robo = Robot()
robo.main()




