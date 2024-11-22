import numpy as np
import cv2

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

    # Define a smaller fixed central region (e.g., 1/8th of the frame size)
    center_x, center_y = width // 2, height // 2
    region_width, region_height = width // 10, height // 10
    x1, y1 = center_x - region_width // 2, center_y - region_height // 2
    x2, y2 = center_x + region_width // 2, center_y + region_height // 2

    # Extract the fixed central region
    central_region = imageFrame[y1:y2, x1:x2]

    # Convert the central region from BGR to HSV color space
    hsvFrame = cv2.cvtColor(central_region, cv2.COLOR_BGR2HSV)

    # Adjust V channel to normalize lighting
    h, s, v = cv2.split(hsvFrame)
    v = cv2.equalizeHist(v)
    hsvFrame = cv2.merge((h, s, v))

    # Set broader range for white color and define mask
    white_lower = np.array([0, 0, 190], np.uint8)  # Lower saturation and value
    white_upper = np.array([180, 50, 255], np.uint8)  # Higher saturation and value
    white_mask = cv2.inRange(hsvFrame, white_lower, white_upper)

    # Detect areas that are not white (colored clothing)
    not_white_mask = cv2.bitwise_not(white_mask)

    # Morphological Transform, Dilation for better contour detection
    kernel = np.ones((5, 5), "uint8")
    white_mask = cv2.dilate(white_mask, kernel)
    not_white_mask = cv2.dilate(not_white_mask, kernel)

    # Debugging: Display the white mask
    cv2.imshow("White Mask", white_mask)

    # Create contours to detect white areas
    contours, _ = cv2.findContours(white_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    detected_color = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 300:
            detected_color = "White"
            break

    # Create contours to detect colored areas
    if detected_color is None:
        contours, _ = cv2.findContours(not_white_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 300:
                detected_color = "Color"
                break

    # Display the detected color
    if detected_color:
        cv2.putText(imageFrame, f"Detected: {detected_color}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    # Draw the smaller central region on the original frame
    cv2.rectangle(imageFrame, (x1, y1), (x2, y2), (0, 255, 255), 2)

    # Display the result
    cv2.imshow("Clothing Sorting - Fixed Region", imageFrame)

    # Exit the loop if 'q' is pressed
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Release the stream and close windows
webcam.release()
cv2.destroyAllWindows()
