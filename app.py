import base64
import json
import cv2
import numpy as np
import pandas as pd
import joblib
import mediapipe as mp
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sock import Sock

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  
sock = Sock(app)  

try:
    model_dict = joblib.load("gesture_model.pkl")
    model = model_dict if not isinstance(model_dict, dict) else model_dict.get('model', model_dict)
    print("🎯 [SUCCESS] gesture_model.pkl loaded smoothly into memory.")
except Exception as e:
    model = None
    print(f"⚠️ [WARNING] Could not load gesture_model.pkl: {e}")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)

latest_prediction = {"gesture": "No Sign", "translation": "No Sign", "confidence": 0.0}

@sock.route('/ws/stream')
def video_stream(ws):
    print("📡 [CONNECTED] Flutter Client hooked into Video Stream Pipeline!")
    global latest_prediction
    while True:
        try:
            message = ws.receive()
            if not message: break
            img_bytes = base64.b64decode(json.loads(message).get('image', '')) if isinstance(message, str) else message
            if not img_bytes: continue

            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None: continue

            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            gesture_label = "No Sign Detected"
            confidence = 0.0

            if results.multi_hand_landmarks and model is not None:
                hand_landmarks = results.multi_hand_landmarks[0]
                data_aux = []
                x_ = [lm.x for lm in hand_landmarks.landmark]
                y_ = [lm.y for lm in hand_landmarks.landmark]
                min_x, min_y = min(x_), min(y_)
                for lm in hand_landmarks.landmark:
                    data_aux.append(lm.x - min_x)
                    data_aux.append(lm.y - min_y)

                if len(data_aux) == model.n_features_in_:
                    gesture_label = str(model.predict([data_aux])[0])
                    confidence = float(np.max(model.predict_proba([data_aux]))) if hasattr(model, "predict_proba") else 1.0
                else:
                    gesture_label = "Shape Mismatch"

            latest_prediction = {"gesture": gesture_label, "translation": gesture_label, "confidence": round(confidence * 100, 2)}
            ws.send(json.dumps(latest_prediction))
        except Exception:
            break
    print("🔌 [DISCONNECTED] Flutter Client disconnected.")

@app.route('/gesture', methods=['GET'])
def get_gesture():
    return jsonify(latest_prediction), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=False, threaded=True)