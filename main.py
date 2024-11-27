import streamlit as st
import cv2
from ultralytics import YOLO
from robot import Robot

# Initialize Streamlit session state for the robot
if "robot" not in st.session_state:
    st.session_state.robot = Robot()

robot = st.session_state.robot
model = YOLO("yolov8x.pt")

st.title("Recycle Sorting with YOLO and Robotic Arm")

# Connect Button
if st.button("Connect to Robot", key="connect_robot"):
    robot.connect()
    if robot.TOKEN:
        st.success(f"Connected to the robot! Token: {robot.TOKEN}")
    else:
        st.error("Failed to retrieve robot token.")

if st.button("Disconnect Robot", key="disconnect_robot"):
    if robot.TOKEN:
        robot.log_off()
        st.success("Robot disconnected.")
    else:
        st.error("Robot is not connected or token is missing!")

if st.button("move Robot", key="move"):
    robot.grab_and_drop((400, 200, 300))


# Video Stream
stream_url = "https://interactions.ics.unisg.ch/61-102/cam5/live-stream"
webcam = cv2.VideoCapture(stream_url)

st.subheader("Live Video Stream")
stframe = st.empty()

if webcam.isOpened():
    while True:
        ret, frame = webcam.read()
        if not ret:
            st.error("Stream disconnected or unavailable.")
            break
        stframe.image(frame, channels="BGR", use_container_width=True)
else:
    st.error("Unable to open the video stream.")

webcam.release()
