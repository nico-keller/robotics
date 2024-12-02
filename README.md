# Recycle Sorting with YOLO and Robotic Arm

This project demonstrates a recycling sorting system using a YOLO model for material detection and a robotic arm for sorting materials into designated areas. The system is implemented using Streamlit for a web interface, OpenCV for video streaming, and a custom Python class to interact with the robotic arm.

---

## Features

- **Robotic Arm Integration**: Connect, control, and disconnect the robotic arm via the Streamlit interface.
- **YOLO-based Material Detection**: Detect materials such as plastic, metal, and glass using YOLOv8.
- **Automated Sorting**: The robotic arm sorts detected materials into predefined positions.
- **Live Video Streaming**: Display a real-time video stream for material detection.
- **REST API Interaction**: Communicates with the robot via a RESTful API for operations like movement, toggling the gripper, and initialization.

---

## Requirements

### Software and Libraries
- Python 3.8+
- [Streamlit](https://streamlit.io/)
- [OpenCV](https://opencv.org/)
- [Ultralytics YOLO](https://github.com/ultralytics/yolov5)
- `requests`
- `numpy`

### Hardware
- A robotic arm with an API endpoint for control
- A camera with live streaming capabilities

---

## Setup and Usage

### 1. Clone the Repository
git clone <repository-url> cd <repository-directory>


### 2. Install Dependencies
Install the required Python libraries:


### 3. Run the Application
Launch the Streamlit app:
streamlit run main.py


### 4. Features in the App
- **Connect to Robot**: Establish a connection with the robotic arm.
- **Disconnect Robot**: Safely disconnect from the robotic arm.
- **Move Robot**: Perform a basic grab-and-drop action.
- **Recycle**: Trigger the automated recycling sorting process.
- **Live Video Stream**: Monitor the detection area in real-time.

---

## Robot Class Functionality

The `Robot` class provides methods for interacting with the robotic arm:
- `connect()`: Connect to the robot and retrieve a session token.
- `log_off()`: Disconnect and log off the robot.
- `toggle()`: Open or close the robotic arm's gripper.
- `move_to_position(x, y, z)`: Move the arm to a specific position.
- `grab_and_drop(position)`: Grab an item and drop it at a specified position.
- `sort_recycling_materials(stream_url)`: Detect and sort materials based on the video feed.

---

## Video Stream Configuration

The video stream URL should be configured in the `stream_url` variable. Replace it with your camera's live stream endpoint.

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or new features.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
