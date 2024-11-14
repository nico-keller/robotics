import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO('yolov8s.pt')

transformation_matrix = np.array([[0.1, 0, 0], [0, 0.1, 0], [0, 0, 1]])

def pixel_to_real(x_pixel, y_pixel):
    pixel_coords = np.array([x_pixel, y_pixel, 1])
    real_coords = np.dot(transformation_matrix, pixel_coords)
    x_real = real_coords[0] / real_coords[2]
    y_real = real_coords[1] / real_coords[2]
    return x_real, y_real

def detect_objects(frame):
    results = model.predict(source=frame, imgsz=640)
    boxes = []
    for result in results[0].boxes:
        x1, y1, x2, y2 = result.xyxy[0].numpy()
        class_id = int(result.cls[0].item())
        confidence = result.conf[0].item()

        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        width = int(x2 - x1)
        height = int(y2 - y1)

        boxes.append({
            "class_id": class_id,
            "confidence": confidence,
            "box": (center_x, center_y, width, height)
        })
    return boxes

video_path = 'IMG_4500.mov'
cap = cv2.VideoCapture(video_path)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    objects = detect_objects(frame)

    for obj in objects:
        x_pixel, y_pixel, _, _ = obj["box"]
        x_real, y_real = pixel_to_real(x_pixel, y_pixel)

        print(f"Object Detected - Class ID: {obj['class_id']}, Confidence: {obj['confidence']:.2f}")
        print(f"Pixel Coordinates: (x: {x_pixel}, y: {y_pixel})")
        print(f"Real-World Coordinates: (x: {x_real:.2f}, y: {y_real:.2f})")
        print("-" * 40)

    for obj in objects:
        x_pixel, y_pixel, width, height = obj["box"]
        top_left = (x_pixel - width // 2, y_pixel - height // 2)
        bottom_right = (x_pixel + width // 2, y_pixel + height // 2)
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
        label = f"ID: {obj['class_id']} Conf: {obj['confidence']:.2f}"
        cv2.putText(frame, label, (x_pixel, y_pixel - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Object Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
