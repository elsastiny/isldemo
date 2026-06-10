import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import random

app = FastAPI(title="SignSpeak AI Translation Engine")

# Simulated list of recognized sign vocabulary tokens
SIGN_VOCABULARY = ["WELCOME", "HELLO", "THANK YOU", "SIGN LANGUAGE", "ASSISTANCE", "GOOD MORNING", "YES", "NO"]

@app.get("/")
def read_root():
    return {"status": "SignSpeak AI Translation Server is running natively."}

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handles real-time ingestion of image frames or coordinate matrices from the 
    Flutter client and streams back translated natural language strings.
    """
    await websocket.accept()
    print(f"📡 [CONNECTED] Flutter Client connected from: {websocket.client.host}")
    
    frame_counter = 0
    
    try:
        while True:
            # Receive incoming raw byte packages sent at 10Hz by your Flutter client
            data = await websocket.receive_bytes()
            frame_counter += 1
            
            # --- COMPUTER VISION / MACHINE LEARNING PIPELINE ENTRY POINT ---
            # Inside a full pipeline, you would process 'data' bytes into an image array:
            # frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            # and pass it to an LSTM, Transformer, or MediaPipe model here.
            # --------------------------------------------------------------

            # To prove the network channel is completely open, simulate a model translation
            # every 15 frames (roughly every 1.5 seconds of sustained sign gestures)
            if frame_counter % 15 == 0:
                predicted_word = random.choice(SIGN_VOCABULARY)
                print(f"🔮 [AI TRANSLATION] Predicted Gesture Sequence: -> {predicted_word}")
                
                # Instantly transmit the plain text string back up to your floating client
                await websocket.send_text(predicted_word)
                
    except WebSocketDisconnect:
        print(f"🔌 [DISCONNECTED] Flutter Client disconnected gracefully.")
    except Exception as e:
        print(f"⚠️ [SERVER ERROR] Error encountered during frame ingestion: {e}")
    finally:
        # Ensure socket cleanup lines execute safely
        try:
            await websocket.close()
        except Exception:
            pass

if __name__ == "__main__":
    # FIXED: Entry point explicitly references 'pythonserver:app' to match your exact file name
    uvicorn.run("pythonserver:app", host="127.0.0.1", port=8000, log_level="info")