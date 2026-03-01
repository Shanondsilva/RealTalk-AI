import threading
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastapi import FastAPI
import uvicorn
import time
import numpy as np
import librosa
import sounddevice as sd
import tkinter as tk
from plyer import notification
import winsound  # Added for the Audio Siren

app = FastAPI()

# --- GLOBAL STATE & COOLDOWN ---
last_alert_time = 0
latest_score = {
    "status": "Initializing...",
    "trust_level": 100,
    "video_status": "Starting...",
    "audio_status": "Starting...",
    "reason": "Calibrating sensors..."
}

# --- PART 1: THE EYES (Video Liveness Detection) ---
def run_detector():
    global latest_score
    try:
        base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1
        )
        detector = vision.FaceLandmarker.create_from_options(options)
        cap = cv2.VideoCapture(0)
        last_blink_time = time.time()

        while cap.isOpened():
            success, frame = cap.read()
            if not success: continue
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            timestamp_ms = int(time.time() * 1000)
            result = detector.detect_for_video(mp_image, timestamp_ms)

            if result.face_landmarks:
                landmarks = result.face_landmarks[0]
                # Eyelid landmark points
                p1, p2 = landmarks[159], landmarks[145]
                eye_dist = ((p1.x - p2.x)**2 + (p1.y - p2.y)**2)**0.5
                
                if eye_dist < 0.015: 
                    last_blink_time = time.time()

                gap = time.time() - last_blink_time
                if gap > 12:
                    latest_score["video_status"] = "SUSPICIOUS (No Blink)"
                else:
                    latest_score["video_status"] = "SECURE (Human)"
            time.sleep(0.05)
    except Exception as e:
        print(f"Video Error: {e}")

# --- PART 2: THE EAR (Audio Analysis & Active Alerts) ---
def analyze_audio():
    global latest_score, last_alert_time
    fs = 22050
    duration = 2
    while True:
        try:
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            sd.wait()
            audio_data = recording.flatten()
            
            # Spectral Flatness: AI voices are 'flatter' than human speech
            flatness = librosa.feature.spectral_flatness(y=audio_data)
            avg_flatness = np.mean(flatness)

            if avg_flatness < 0.005: 
                latest_score["audio_status"] = "SUSPICIOUS (Robotic)"
            else:
                latest_score["audio_status"] = "SECURE (Natural)"
            
            # Master Multi-Modal Logic
            if "SUSPICIOUS" in latest_score["video_status"] or "SUSPICIOUS" in latest_score["audio_status"]:
                latest_score["trust_level"] = 35
                latest_score["status"] = "SUSPICIOUS"
                latest_score["reason"] = "Deepfake markers detected."
                
                # TRIGGER ACTIVE ALERTS (Notification + Siren)
                current_time = time.time()
                if current_time - last_alert_time > 30: # 30-second cooldown
                    # 1. Desktop Notification
                    notification.notify(
                        title="⚠️ REALTALK ALERT",
                        message="Deepfake risk detected! Check your security HUD.",
                        app_name="RealTalk AI",
                        timeout=10
                    )
                    # 2. Audio Siren (Beep)
                    winsound.Beep(1000, 500) 
                    
                    last_alert_time = current_time
            else:
                latest_score["trust_level"] = 98
                latest_score["status"] = "SECURE"
                latest_score["reason"] = "Biological markers look natural."
                
        except Exception as e:
            latest_score["audio_status"] = f"Mic Error: {str(e)}"
        time.sleep(0.5)

# --- PART 3: THE OVERLAY (HUD Display) ---
def start_overlay():
    root = tk.Tk()
    root.title("RealTalk HUD")
    root.attributes('-topmost', True) # Always on top
    root.overrideredirect(True)       # No title bar
    root.geometry("220x75+30+30")     # Positioned in top-left
    root.configure(bg='#121212')      # Dark 'Security' theme
    root.attributes('-alpha', 0.85)   # Semi-transparent

    tk.Label(root, text="REALTALK DEFENSE", fg="#888888", bg="#121212", font=("Courier", 8)).pack(pady=(5,0))
    label_status = tk.Label(root, text="SCANNING...", fg="white", bg="#121212", font=("Arial", 11, "bold"))
    label_status.pack()
    label_trust = tk.Label(root, text="TRUST: 100%", fg="white", bg="#121212", font=("Arial", 9))
    label_trust.pack(pady=(0,5))

    def update_gui():
        # Visual color cues
        color = "#00ff7f" if latest_score["status"] == "SECURE" else "#ff4444"
        label_status.config(text=latest_score["status"], fg=color)
        label_trust.config(text=f"TRUST: {latest_score['trust_level']}%", fg=color)
        root.after(500, update_gui)

    update_gui()
    root.mainloop()

# --- PART 4: THE RADIO (API Endpoint) ---
@app.get("/status")
async def get_status():
    return latest_score

if __name__ == "__main__":
    # Launching parallel sensor threads
    threading.Thread(target=run_detector, daemon=True).start()
    threading.Thread(target=analyze_audio, daemon=True).start()
    threading.Thread(target=start_overlay, daemon=True).start()
    
    # Starting the local API server
    uvicorn.run(app, host="127.0.0.1", port=8000)