import cv2
import numpy as np

left_history = []
right_history = []

# ----------------------- Region Of Interest -----------------------
def region_of_interest(img):
    height, width = img.shape
    polygons = np.array([
        [(int(width * 0.05), height),
         (int(width * 0.95), height),
         (int(width * 0.60), int(height * 0.62)),
         (int(width * 0.40), int(height * 0.62))]
    ])
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, polygons, 255)
    return cv2.bitwise_and(img, mask)

# ----------------------- Draw Lane Lines Smoothly -----------------------
def draw_lanes(img, lines):
    global left_history, right_history
    left, right = [], []

    if lines is None:
        return img

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 == x1:
            continue

        slope = (y2 - y1) / (x2 - x1)

        if slope < -0.25:
            left.append((x1, y1, x2, y2))
        elif slope > 0.25:
            right.append((x1, y1, x2, y2))

    def average(group):
        if len(group) == 0:
            return None
        xs, ys = [], []
        for x1, y1, x2, y2 in group:
            xs += [x1, x2]
            ys += [y1, y2]
        return np.polyfit(xs, ys, 1)

    L = average(left)
    if L is None and len(left_history) > 0:
        L = left_history[-1]
    R = average(right)
    if R is None and len(right_history) > 0:
        R = right_history[-1]

    if L is not None:
        left_history.append(L)
    if R is not None:
        right_history.append(R)

    left_history[:] = left_history[-8:]
    right_history[:] = right_history[-8:]

    height = img.shape[0]
    y1, y2 = height, int(height * 0.62)

    def draw(side, color):
        if side is None:
            return
        slope, intercept = side
        x1 = int((y1 - intercept) / slope)
        x2 = int((y2 - intercept) / slope)
        cv2.line(img, (x1, y1), (x2, y2), color, 10)

    draw(left_history[-1] if left_history else None, (0, 255, 0))
    draw(right_history[-1] if right_history else None, (0, 255, 0))

    return img

# ----------------------- Lane Processing -----------------------
def process_lane(frame):
    frame = cv2.resize(frame, (960, 540))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 40, 120)

    masked = region_of_interest(edges)
    lines = cv2.HoughLinesP(masked, 1, np.pi/180, 40, minLineLength=40, maxLineGap=180)

    lane_img = np.zeros_like(frame)
    draw_lanes(lane_img, lines)

    return cv2.addWeighted(frame, 0.8, lane_img, 1, 0)

# ----------------------- Object Detection Using MOG2 -----------------------
subtractor = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=40)

# ----------------------- Main -----------------------
def main():
    cap = cv2.VideoCapture("videos/combined_detection.mp4")  # change your video name here

    if not cap.isOpened():
        print("Error: Could not open video")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        lane_frame = process_lane(frame)

        mask = subtractor.apply(lane_frame)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, (5, 5))
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 1200:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(lane_frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
            cv2.putText(lane_frame, "Vehicle", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        cv2.imshow("Combined Lane + Object Detection", lane_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
