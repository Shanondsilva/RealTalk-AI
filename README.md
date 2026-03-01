# RealTalk AI: Multi-Modal Deepfake Defense 🛡️

RealTalk is a real-time security suite designed to detect AI-generated video and audio clones during live calls. It uses a "Defense-in-Depth" strategy, analyzing both biological and acoustic markers.

## 🚀 Features
* **Liveness Detection:** Monitors eye-blink frequency using MediaPipe (detects static facial renders).
* **Acoustic Analysis:** Uses Librosa to detect "Spectral Flatness" (identifies robotic/tonal signatures in AI voice clones).
* **Security HUD:** An "Always-on-Top" transparent overlay for real-time monitoring during meetings.
* **Active Alerting:** Native Windows notifications for high-risk detection.
* **AI Orchestration:** Integrated with Flowise for LLM-based security reporting.

## 🛠️ Tech Stack
* **Language:** Python 3.14
* **AI/CV:** MediaPipe, Librosa, NumPy
* **API:** FastAPI, Uvicorn
* **UI:** Tkinter (HUD), Plyer (Notifications)
* **Orchestration:** Flowise / LangChain

## 🧠 How it Works
1. **Visual Layer:** Humans blink roughly every 4-6 seconds. Deepfakes often skip this. RealTalk flags any gap > 12 seconds.
2. **Audio Layer:** Human speech is "noisy." AI voices are "tonal." RealTalk calculates the spectral flatness; if it's too perfect, it's flagged as synthetic.
3. **Decision Engine:** If either marker is suspicious, the Trust Level drops, and an alert is triggered.