# Hand Gesture Volume Control

Control your **Windows 10/11 system volume** in real time using hand
gestures captured from your webcam — no mouse, no keyboard, just your
thumb and index finger.

Built with **OpenCV**, **MediaPipe Hands**, and **Pycaw** (Windows Core
Audio API bindings via `comtypes`).

---

## How it works

1. OpenCV captures live video from your webcam.
2. MediaPipe Hands detects **1 hand** and tracks all **21 landmarks**.
3. The distance between **Thumb Tip (landmark 4)** and **Index Finger Tip
   (landmark 8)** is measured in pixels.
4. That distance is mapped to a 0–100% volume range and smoothed to avoid
   jitter.
5. Pycaw sets the actual **Windows system volume** using
   `IAudioEndpointVolume.SetMasterVolumeLevel`.
6. A live overlay shows the hand skeleton, the thumb–index line, a volume
   bar, the volume percentage, and the current FPS.

**Pinch fingers together → volume down. Spread fingers apart → volume up.**

---

## Project structure

```
HandVolumeControl/
├── app.py                  # Main application (run this)
├── HandTrackingModule.py   # Reusable MediaPipe hand-tracking wrapper
├── requirements.txt        # Python dependencies
└── README.md                # This file
```

---

## Requirements

- **OS:** Windows 10 or Windows 11 (Pycaw depends on the Windows Core
  Audio API and will not work on macOS/Linux)
- **Python:** 3.11 (64-bit recommended)
- A working webcam

---

## Installation

1. **Create and activate a virtual environment** (recommended):

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```powershell
   pip install -r requirements.txt
   ```

   Package versions used and tested for this project:

   | Package       | Version   |
   | ------------- | --------- |
   | opencv-python | 4.10.0.84 |
   | mediapipe     | 0.10.14   |
   | pycaw         | 20240210  |
   | numpy         | 1.26.4    |
   | comtypes      | 1.4.6     |

---

## Usage

Run the app from the project folder:

```powershell
python app.py
```

- A window titled **"Hand Gesture Volume Control"** will open showing your
  webcam feed.
- Show **one hand** to the camera with your palm facing it.
- Move your **thumb** and **index finger** apart or together to change the
  volume — the on-screen bar and percentage update live, and your actual
  Windows system volume changes with it.
- Press **`Q`** at any time to quit.

---

## Configuration

You can tune the gesture sensitivity at the top of `app.py`:

```python
CAM_INDEX = 0                # change if you have multiple cameras
MIN_HAND_DISTANCE = 25       # pixel distance mapped to 0% volume
MAX_HAND_DISTANCE = 200      # pixel distance mapped to 100% volume
SMOOTHING = 5                # higher = smoother but slower response
```

- If the volume maxes out too easily, **increase** `MAX_HAND_DISTANCE`.
- If it's hard to reach 0%, **decrease** `MIN_HAND_DISTANCE`.
- If the volume bar feels jittery, **increase** `SMOOTHING`.
- If it feels laggy, **decrease** `SMOOTHING`.

---

## Troubleshooting

**"Could not open webcam"**

- Make sure no other app (Zoom, Teams, etc.) is using the camera.
- Try changing `CAM_INDEX` to `1` or `2` if you have multiple cameras.

**"Could not import pycaw/comtypes"**

- This project only runs on Windows. Confirm you're on Windows 10/11 and
  ran `pip install -r requirements.txt` inside the correct environment.

**"Could not access Windows audio endpoint volume"**

- Ensure a default playback device is set in Windows Sound settings.
- Try running the terminal/IDE as Administrator if permission errors
  persist.

**Low FPS / laggy detection**

- Close other camera- or GPU-heavy applications.
- Lower `FRAME_WIDTH` / `FRAME_HEIGHT` in `app.py` (e.g., 480×360).
- Set `model_complexity=0` when constructing `HandDetector` in `app.py`
  for a faster (slightly less accurate) model.

**Hand not detected**

- Ensure good, even lighting and keep your hand fully in frame.
- Avoid a cluttered or skin-tone-matching background if possible.

---

## Notes on the MediaPipe API

This project uses MediaPipe's stable `mediapipe.solutions.hands` API
(via `HandTrackingModule.py`), which is the widely supported and
documented interface for hand landmark detection in the current
MediaPipe stable release line. It provides real-time detection of 21
3D hand landmarks per hand with confidence-based detection and
tracking, exactly as used in `app.py`.

---

## License

Free to use, modify, and distribute for personal or educational purposes.
