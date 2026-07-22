import sys
import time
import cv2
import numpy as np
import HandTrackingModule as htm

# ---- Windows-only imports (Pycaw / comtypes) --------------------------------
try:
    import comtypes
    from comtypes import CLSCTX_ALL
    from ctypes import cast, POINTER
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    comtypes.CoInitialize()
except ImportError:
    print(
        "ERROR: Could not import pycaw/comtypes.\n"
        "This project requires Windows 10/11 and the packages listed in "
        "requirements.txt.\n"
        "Install them with:  pip install -r requirements.txt"
    )
    sys.exit(1)


# ------------------------------- Configuration -------------------------------
CAM_INDEX = 0                # Webcam index (0 = default camera)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

MIN_HAND_DISTANCE = 25        # px: distance treated as 0% volume (adjust to taste)
MAX_HAND_DISTANCE = 200       # px: distance treated as 100% volume (adjust to taste)

SMOOTHING = 5                 # higher = smoother / slower response
VOLUME_BAR_TOP = 150
VOLUME_BAR_BOTTOM = 400
VOLUME_BAR_X = 50


def get_volume_interface():
    
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume


def open_camera(index: int) -> cv2.VideoCapture:
    
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # CAP_DSHOW = fast, reliable on Windows
    if not cap.isOpened():
        # Fallback: try default backend
        cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print(
            f"ERROR: Could not open webcam at index {index}.\n"
            "Please check that:\n"
            "  - A webcam is connected\n"
            "  - No other application is using the camera\n"
            "  - The correct CAM_INDEX is set in app.py"
        )
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return cap


def main():
    # ---- Set up system volume control ----
    try:
        volume_interface = get_volume_interface()
        current = volume_interface.GetMasterVolumeLevelScalar()
        is_muted = volume_interface.GetMute()
        default_device_name = AudioUtilities.GetSpeakers().FriendlyName if hasattr(
            AudioUtilities.GetSpeakers(), "FriendlyName"
        ) else "Unknown"
        print(f"Audio endpoint OK. Current system volume: {current * 100:.0f}%")
        print(f"Muted: {bool(is_muted)}")
        print(f"Default playback device: {default_device_name}")
        if is_muted:
            print("NOTE: System audio is currently MUTED. Unmute it in Windows first.")
    except Exception as exc:  # noqa: BLE001 - want to catch any COM error gracefully
        print(f"ERROR: Could not access Windows audio endpoint volume.\nDetails: {exc}")
        sys.exit(1)

    # ---- Set up camera and hand detector ----
    cap = open_camera(CAM_INDEX)
    detector = htm.HandDetector(max_hands=1, detection_confidence=0.7, tracking_confidence=0.7)

    prev_time = 0.0
    smoothed_vol_percent = 0
    vol_percent = 0
    vol_bar_y = VOLUME_BAR_BOTTOM

    print("Hand Gesture Volume Control started. Press 'Q' in the video window to quit.")

    try:
        while True:
            success, frame = cap.read()
            if not success or frame is None:
                print("WARNING: Failed to read frame from webcam. Retrying...")
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)  # mirror view feels natural

            frame = detector.findHands(frame, draw=True)
            landmark_list = detector.findPosition(frame, draw=False)

            if landmark_list:
                # Thumb tip = landmark 4, Index tip = landmark 8
                length, frame, line_info = detector.findDistance(4, 8, frame, draw=True)

                if length != -1:
                    # Map hand distance -> volume percentage (0-100)
                    length = np.clip(length, MIN_HAND_DISTANCE, MAX_HAND_DISTANCE)
                    vol_percent = np.interp(
                        length, [MIN_HAND_DISTANCE, MAX_HAND_DISTANCE], [0, 100]
                    )

                    # Smooth the value to avoid jittery volume changes
                    smoothed_vol_percent += (vol_percent - smoothed_vol_percent) / SMOOTHING
                    smoothed_vol_percent = float(np.clip(smoothed_vol_percent, 0, 100))

                    # Apply directly as a 0.0-1.0 scalar (more reliable than the
                    # dB-based API across different audio drivers)
                    volume_interface.SetMasterVolumeLevelScalar(
                        float(smoothed_vol_percent) / 100.0, None
                    )

                    # Debug: confirm gesture -> volume is actually happening.
                    # Remove or comment out once you've confirmed it's working.
                    print(
                        f"dist={length:6.1f}px  vol={smoothed_vol_percent:5.1f}%  "
                        f"set_scalar={smoothed_vol_percent / 100.0:.2f}"
                    )

                    # Visual feedback: highlight the midpoint when pinched very close
                    if length <= MIN_HAND_DISTANCE + 5:
                        cx, cy = line_info[4], line_info[5]
                        cv2.circle(frame, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                    vol_bar_y = int(
                        np.interp(
                            smoothed_vol_percent, [0, 100], [VOLUME_BAR_BOTTOM, VOLUME_BAR_TOP]
                        )
                    )

            # ---- Draw the volume bar ----
            cv2.rectangle(
                frame,
                (VOLUME_BAR_X, VOLUME_BAR_TOP),
                (VOLUME_BAR_X + 35, VOLUME_BAR_BOTTOM),
                (255, 0, 0),
                3,
            )
            cv2.rectangle(
                frame,
                (VOLUME_BAR_X, vol_bar_y),
                (VOLUME_BAR_X + 35, VOLUME_BAR_BOTTOM),
                (255, 0, 0),
                cv2.FILLED,
            )
            cv2.putText(
                frame,
                f"{int(smoothed_vol_percent)} %",
                (VOLUME_BAR_X - 10, VOLUME_BAR_TOP - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 0, 0),
                2,
            )

            # ---- FPS calculation ----
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if prev_time else 0.0
            prev_time = curr_time
            cv2.putText(
                frame,
                f"FPS: {int(fps)}",
                (frame.shape[1] - 150, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                "Press 'Q' to quit",
                (10, frame.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1,
            )

            cv2.imshow("Hand Gesture Volume Control", frame)

            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                print("Exit key pressed. Shutting down...")
                break

    except KeyboardInterrupt:
        print("Interrupted by user (Ctrl+C). Shutting down...")

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()