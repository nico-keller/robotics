import streamlit as st
import cv2
import asyncio
from ultralytics import YOLO
from robot import Robot

# Initialize Streamlit session state for the robot and frame
if "robot" not in st.session_state:
    st.session_state.robot = Robot()

robot = st.session_state.robot
models = [YOLO("recycling.pt"), YOLO("yolov8x.pt")]

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

if st.button("Move Robot", key="move_robot"):
    robot.grab_and_drop((400, 200, 300))
    st.success("Robot moved successfully!")

if st.button("Recycle", key="recycle"):
    robot.sort_recycling_materials("https://interactions.ics.unisg.ch/61-102/cam5/live-stream")
    st.write("Recycling in progress...")

stream_url = "https://interactions.ics.unisg.ch/61-102/cam5/live-stream"
webcam = cv2.VideoCapture(stream_url)

st.subheader("Live Video Stream")
stframe = st.empty()


async def stream_video():
    while True:
        ret, frame = webcam.read()
        if not ret:
            stframe.text("Stream disconnected or unavailable.")
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

        detection_region = frame[y1:y2, x1:x2]
        best_detection = None  # Store the best detection

        # Process detection region with both models
        for model in models:
            results = model(detection_region, conf=0.5)

            for result in results:
                for box in result.boxes:
                    conf = float(box.conf.item())
                    class_id = int(box.cls.item())
                    b = box.xyxy[0].cpu().numpy()
                    b[0] += x1
                    b[1] += y1
                    b[2] += x1
                    b[3] += y1

                    if best_detection is None or conf > best_detection['conf']:
                        best_detection = {
                            'conf': conf,
                            'class_id': class_id,
                            'box': b,
                            'model_names': model.names
                        }

        # If there's a best detection, draw it on the frame
        if best_detection:
            b = best_detection['box']
            conf = best_detection['conf']
            class_id = best_detection['class_id']
            label = f"{best_detection['model_names'][class_id]} {conf:.2f}"

            cv2.rectangle(frame,
                          (int(b[0]), int(b[1])),
                          (int(b[2]), int(b[3])),
                          (0, 255, 0),
                          2)
            cv2.putText(frame, label,
                        (int(b[0]), int(b[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 255, 0),
                        2)

        # Display the frame
        stframe.image(frame, channels="BGR", use_container_width=True)
        await asyncio.sleep(0.03)  # Control the update rate


async def main():
    await stream_video()


asyncio.run(main())

webcam.release()
