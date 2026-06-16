# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) # Loosen CORS safety constraints for local loops

# Clear global buffers
current_frame_b64 = None
latest_prediction = {"gesture": "", "translation": "", "confidence": 0.0}

@app.route('/process_frame', methods=['POST'])
def process_frame():
    global current_frame_b64
    data = request.get_json()
    if data and 'image' in data:
        current_frame_b64 = data['image'] # Stores frame from browser extension
    return jsonify({"status": "success"}), 200

# --- THIS IS THE ROUTE THAT WAS DROPPING A 404 ERROR ---
@app.route('/get_scraped_frame_string', methods=['GET'])
def get_scraped_frame_string():
    global current_frame_b64
    return jsonify({"image": current_frame_b64}), 200

@app.route('/update_gesture', methods=['POST'])
def update_gesture():
    global latest_prediction
    data = request.get_json()
    if data:
        latest_prediction = data # Receives prediction text from AI engine
    return jsonify({"status": "success"}), 200

@app.route('/gesture', methods=['GET'])
def get_gesture():
    global latest_prediction
    return jsonify(latest_prediction), 200 # Serves prediction text to overlay

if __name__ == '__main__':
    # Force alignment down the loopback corridor
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)