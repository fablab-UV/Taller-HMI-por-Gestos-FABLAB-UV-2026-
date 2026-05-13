import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import hand_landmarker
from pathlib import Path
import time

model_path = Path(__file__).resolve().parents[1] / "hand_landmarker.task"
if not model_path.exists():
    raise FileNotFoundError("No se encontro hand_landmarker.task en la raiz del proyecto")

base_options = python.BaseOptions(model_asset_path=str(model_path))
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)
landmarker = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la camara")

try:
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.monotonic() * 1000)
        results = landmarker.detect_for_video(mp_image, timestamp_ms)

        h, w, _ = frame.shape
        x1, y1 = w - 160, 20
        x2, y2 = w - 20, 160
        boton_color = (0, 255, 0)

        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    hand_landmarker.HandLandmarksConnections.HAND_CONNECTIONS,
                    drawing_styles.get_default_hand_landmarks_style(),
                    drawing_styles.get_default_hand_connections_style(),
                )

                indice = hand_landmarks[8]
                px = int(indice.x * w)
                py = int(indice.y * h)
                cv2.circle(frame, (px, py), 10, (255, 0, 0), -1)

                if x1 < px < x2 and y1 < py < y2:
                    boton_color = (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), boton_color, 2)

        cv2.imshow("Slide 22 - Colision", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
finally:
    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()
