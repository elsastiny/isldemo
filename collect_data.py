import cv2
import mediapipe as mp
import csv
import os

# MediaPipe setup
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

mp_draw = mp.solutions.drawing_utils

# Webcam
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# CSV file
file_name = "gesture_data.csv"

# Create CSV header if file doesn't exist
if not os.path.exists(file_name):

    header = ["gesture", "hand"]

    for i in range(21):
        header += [f"x{i}", f"y{i}"]

    with open(file_name, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

print("Press:")
print("H = HELLO")
print("Y = YES")
print("P = PEACE")
print("S = STOP")

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)
    gesture_label = None

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_label = f"Hand{idx + 1}"
            if results.multi_handedness and idx < len(results.multi_handedness):
                hand_label = results.multi_handedness[idx].classification[0].label

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.putText(
        frame,
        "H=HELLO Y=YES P=PEACE S=STOP",
        (10, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.imshow("Collect Gesture Data", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('h'):
        gesture_label = "HELLO"
    elif key == ord('y'):
        gesture_label = "YES"
    elif key == ord('p'):
        gesture_label = "PEACE"
    elif key == ord('s'):
        gesture_label = "STOP"

    if gesture_label and results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_label = f"Hand{idx + 1}"
            if results.multi_handedness and idx < len(results.multi_handedness):
                hand_label = results.multi_handedness[idx].classification[0].label

            row = [gesture_label, hand_label]
            for landmark in hand_landmarks.landmark:
                row.append(landmark.x)
                row.append(landmark.y)

            with open(file_name, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

        print(f"Saved: {gesture_label} for {len(results.multi_hand_landmarks)} hand(s)")

    # Quit
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()