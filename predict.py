import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
import joblib
from PIL import Image, ImageDraw, ImageFont

# =====================================
# LOAD MODEL
# =====================================
model = joblib.load("gesture_model.pkl")

# Minimum probability required to accept a prediction (increase to reduce false/low-confidence predictions)
CONFIDENCE_THRESHOLD = 0.7

# Translation cache to avoid repeated network calls for the same label
translation_cache = {}

# =====================================
# MEDIAPIPE
# =====================================
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

mp_draw = mp.solutions.drawing_utils

# =====================================
# CAMERA
# =====================================
cap = cv2.VideoCapture(0)

# =====================================
# BUILD DATAFRAME
# =====================================
def build_dataframe(landmarks, hand_label):
    columns = []
    row = []

    for i in range(21):
        columns.extend([
            f"x{i}",
            f"y{i}"
        ])
        row.extend([
            landmarks[i * 2],
            landmarks[i * 2 + 1]
        ])

    columns.extend([
        "hand_Left",
        "hand_Right"
    ])
    row.extend([
        1 if hand_label == "Left" else 0,
        1 if hand_label == "Right" else 0
    ])

    df = pd.DataFrame([row], columns=columns)

    return df.reindex(
        columns=model.feature_names_in_,
        fill_value=0
    )

# =====================================
# TRANSLATOR
# =====================================
from googletrans import Translator

translator = Translator()

# =====================================
# MALAYALAM FONT
# =====================================
def load_malayalam_font(size=32):
    possible_fonts = [
        "/usr/share/fonts/truetype/noto/NotoSansMalayalam-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifMalayalam-Regular.ttf",
        "/usr/share/fonts/truetype/smc/Meera.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]

    for path in possible_fonts:
        try:
            mal = ImageFont.truetype(path, size)
            return mal
        except:
            continue

    return ImageFont.load_default()


mal_font = load_malayalam_font(32)

# English font (for labels)
def load_english_font(size=20):
    possible = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    for p in possible:
        try:
            f = ImageFont.truetype(p, size)
            return f
        except:
            continue
    return ImageFont.load_default()

eng_font = load_english_font(20)

# =====================================
# MAIN LOOP
# =====================================
while True:
    success, frame = cap.read()

    if not success:
        continue

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(
            results.multi_hand_landmarks
        ):
            hand_label = "Unknown"

            if results.multi_handedness:
                hand_label = results.multi_handedness[
                    idx
                ].classification[0].label

            # Draw landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Extract landmarks
            landmark_list = []

            for lm in hand_landmarks.landmark:
                landmark_list.append(lm.x)
                landmark_list.append(lm.y)

            # Build dataframe
            df = build_dataframe(
                landmark_list,
                hand_label
            )

            # Predict
            prediction = model.predict(df)[0]
            probability = float(np.max(model.predict_proba(df)[0]))

            # Apply confidence threshold to reduce low-confidence translations
            if probability >= CONFIDENCE_THRESHOLD:
                final_label = prediction
                # Use cached translation if available
                if final_label in translation_cache:
                    translated = translation_cache[final_label]
                else:
                    try:
                        translated = translator.translate(final_label, dest="ml").text
                    except Exception:
                        translated = final_label
                    translation_cache[final_label] = translated
            else:
                final_label = "Unknown"
                translated = ""

            # Display
            # Convert frame to PIL for text rendering
            img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img_pil)

            # Display gesture and confidence with PIL (English)
            draw.text((10, 40), f"Gesture: {final_label}", font=eng_font, fill=(0, 255, 0))
            draw.text((10, 80), f"Confidence: {probability:.2f}", font=eng_font, fill=(255, 255, 0))
            # Malayalam translation (render with Malayalam-capable font)
            if translated:
                draw.text((10, 120), f"{translated}", font=mal_font, fill=(255, 0, 0))

            # Convert back to OpenCV format
            frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    else:
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text((10, 40), "NO HAND DETECTED", font=eng_font, fill=(0, 0, 255))
        frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    cv2.imshow(
        "ISL Predictor",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()

cv2.destroyAllWindows()