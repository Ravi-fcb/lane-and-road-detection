import cv2
import numpy as np

def main():
    cap = cv2.VideoCapture("videos/object_detection.mp4")  # change name if needed

    if not cap.isOpened():
        print("Error: Could not open video")
        return

    # Background subtractor to detect moving objects
    subtractor = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=40)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (960, 540))
        mask = subtractor.apply(frame)

        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, None, iterations=2)

        # Find moving object contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 800:   # filter small noise
                continue

            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
            cv2.putText(frame, "Vehicle", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Object Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
