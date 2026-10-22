import cv2
import numpy as np

left_history = []
right_history = []

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

def draw_lanes(img, lines):
    global left_history, right_history
    left_lines = []
    right_lines = []

    if lines is None:
        return
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 == x1:
            continue
        
        slope = (y2 - y1) / (x2 - x1)

        if slope < -0.25:
            left_lines.append((x1, y1, x2, y2))
        elif slope > 0.25:
            right_lines.append((x1, y1, x2, y2))

    def average(group):
        if len(group) == 0:
            return None
        xs, ys = [], []
        for x1, y1, x2, y2 in group:
            xs += [x1, x2]
            ys += [y1, y2]
        return np.polyfit(xs, ys, 1)

    # FIXED fallback error using correct conditional logic
    left = average(left_lines)
    if left is None and len(left_history) > 0:
        left = left_history[-1]

    right = average(right_lines)
    if right is None and len(right_history) > 0:
        right = right_history[-1]

    if left is not None:
        left_history.append(left)
    if right is not None:
        right_history.append(right)

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

def process_frame(frame):
    frame = cv2.resize(frame, (960, 540))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 40, 120)

    masked = region_of_interest(edges)

    lines = cv2.HoughLinesP(
        masked,
        1,
        np.pi / 180,
        threshold=40,
        minLineLength=35,
        maxLineGap=180
    )

    lane_img = np.zeros_like(frame)
    draw_lanes(lane_img, lines)

    return cv2.addWeighted(frame, 0.8, lane_img, 1, 0)

def main():
    cap = cv2.VideoCapture("videos/lane_detection.mp4")  # CHANGE PATH AS NEEDED

    if not cap.isOpened():
        print("Error: could not open video file.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        output = process_frame(frame)
        cv2.imshow("Lane Detection (Day)", output)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
