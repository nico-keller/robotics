import cv2
from ultralytics import YOLO

# Load the YOLO model
model = YOLO("yolov8x.pt")  # Ensure the 'recycle.pt' file is in the working directory or provide its full path


def detect_recycling_material(frame, region):
    """
    Detects recycling materials (e.g., metal, glass, plastic) in the specified region of the frame.

    Parameters:
        frame (numpy.ndarray): The current video frame.
        region (tuple): The bounding box of the region (x1, y1, x2, y2) to analyze.

    Returns:
        list: Detected material types in the region.
    """
    x1, y1, x2, y2 = region
    central_region = frame[y1:y2, x1:x2]

    # Perform YOLO detection
    results = model(central_region, conf=0.5)  # Adjust confidence threshold as needed

    detected_materials = []
    for result in results:
        for box in result.boxes:
            class_id = box.cls.item()  # Get the class index
            material_name = model.names[int(class_id)]  # Map index to class name
            detected_materials.append(material_name)

    return detected_materials


# Replace webcam input with the video stream URL
stream_url = "https://interactions.ics.unisg.ch/61-102/cam5/live-stream"
webcam = cv2.VideoCapture(stream_url)

# Check if the stream is available
if not webcam.isOpened():
    print("Error: Unable to open stream.")
    exit()

# Start a while loop
while True:
    # Read the video stream
    ret, imageFrame = webcam.read()
    if not ret:
        print("Stream disconnected or unavailable.")
        break

    # Get the dimensions of the frame
    height, width, _ = imageFrame.shape

    # Define a slightly larger fixed central region and shift it upwards and to the left
    center_x, center_y = width // 2, height // 2
    shift_x, shift_y = 35, 40  # Shift the region upwards and to the left (adjust as needed)

    # Increase the region size by 20%
    region_width, region_height = int(width // 8), int(height // 8 * 1.5)
    x1 = center_x - region_width // 2 - shift_x
    y1 = center_y - region_height // 2 - shift_y
    x2 = center_x + region_width // 2 - shift_x
    y2 = center_y + region_height // 2 - shift_y
    region = (x1, y1, x2, y2)

    # Ensure the region stays within frame bounds
    x1, y1 = max(x1, 0), max(y1, 0)
    x2, y2 = min(x2, width), min(y2, height)
    region = (x1, y1, x2, y2)

    # Call the detection function
    materials = detect_recycling_material(imageFrame, region)

    # Display detected materials
    if materials:
        detected_text = ", ".join(materials)
        cv2.putText(imageFrame, f"Detected: {detected_text}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    # Draw the shifted and larger region on the original frame
    cv2.rectangle(imageFrame, (x1, y1), (x2, y2), (0, 255, 255), 2)

    # Display the result
    cv2.imshow("Recycling Detection - Fixed Region", imageFrame)

    # Exit the loop if 'q' is pressed
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Release the stream and close windows
webcam.release()
cv2.destroyAllWindows()
