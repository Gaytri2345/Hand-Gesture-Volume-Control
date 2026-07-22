import math
import cv2
import mediapipe as mp


class HandDetector:
    """Detects a hand (or hands) in an image/frame and exposes landmark data."""

    def __init__(
        self,
        mode: bool = False,
        max_hands: int = 1,
        model_complexity: int = 1,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.7,
    ):
        """
        Args:
            mode: If True, treats every frame as a new image (no tracking
                  between frames). False (default) enables tracking, which
                  is faster and smoother for video streams.
            max_hands: Maximum number of hands to detect.
            model_complexity: 0 or 1. 1 is more accurate, 0 is faster.
            detection_confidence: Minimum confidence for initial detection.
            tracking_confidence: Minimum confidence for tracking landmarks
                                  across frames.
        """
        self.mode = mode
        self.max_hands = max_hands
        self.model_complexity = model_complexity
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence,
        )

        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles

        self.results = None
        self.landmark_list = []

    def findHands(self, frame, draw: bool = True):
        
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_rgb.flags.writeable = False
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw_styles.get_default_hand_landmarks_style(),
                        self.mp_draw_styles.get_default_hand_connections_style(),
                    )
        return frame

    def findPosition(self, frame, hand_no: int = 0, draw: bool = True):
        """
        Extracts pixel coordinates for all 21 landmarks of a chosen hand.

        Args:
            frame: BGR image (used to convert normalized coords to pixels).
            hand_no: Index of the hand to read (0 = first detected hand).
            draw: If True, draws a small circle on each landmark.

        Returns:
            A list of [id, x, y] for each of the 21 landmarks.
            Empty list if no hand / hand_no is detected.
        """
        self.landmark_list = []

        if self.results and self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                hand = self.results.multi_hand_landmarks[hand_no]
                h, w, _ = frame.shape

                for lm_id, lm in enumerate(hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.landmark_list.append([lm_id, cx, cy])
                    if draw:
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        return self.landmark_list

    def findDistance(self, p1: int, p2: int, frame, draw: bool = True, r: int = 8, t: int = 3):
        """
        Computes the euclidean distance between two landmarks.

        Args:
            p1, p2: Landmark IDs (e.g. 4 = thumb tip, 8 = index tip).
            frame: BGR image to draw on.
            draw: Whether to draw the connecting line and endpoint circles.
            r: Radius of the endpoint circles.
            t: Thickness of the connecting line.

        Returns:
            (length, frame, [x1, y1, x2, y2, cx, cy])
            length is -1 if the requested landmarks are unavailable.
        """
        if not self.landmark_list or len(self.landmark_list) <= max(p1, p2):
            return -1, frame, []

        x1, y1 = self.landmark_list[p1][1], self.landmark_list[p1][2]
        x2, y2 = self.landmark_list[p2][1], self.landmark_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.circle(frame, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(frame, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(frame, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        return length, frame, [x1, y1, x2, y2, cx, cy]
