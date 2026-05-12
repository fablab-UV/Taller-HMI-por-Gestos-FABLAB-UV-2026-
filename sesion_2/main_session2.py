import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import hand_landmarker
from pathlib import Path
import time
import urllib.request
import serial

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

MODEL_PATH = Path(__file__).resolve().parents[1] / "hand_landmarker.task"

PUERTO_SERIAL = "COM3"
BAUDIOS = 9600


def ensure_model(path: Path) -> Path:
    if path.exists():
        return path
    try:
        urllib.request.urlretrieve(MODEL_URL, path)
    except Exception as e:
        print("Error descargando modelo:", e)
    return path


def open_serial(port: str, baudrate: int):
    try:
        return serial.Serial(port, baudrate, timeout=1)
    except Exception as e:
        print("No se pudo abrir el puerto serial:", e)
        return None


def count_fingers(landmarks, handedness_label: str) -> int:
    # Indices de landmarks MediaPipe
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]

    index_tip = landmarks[8]
    index_pip = landmarks[6]

    middle_tip = landmarks[12]
    middle_pip = landmarks[10]

    ring_tip = landmarks[16]
    ring_pip = landmarks[14]

    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]

    fingers = 0

    if handedness_label == "Right":
        if thumb_tip.x > thumb_ip.x:
            fingers += 1
    else:
        if thumb_tip.x < thumb_ip.x:
            fingers += 1

    if index_tip.y < index_pip.y:
        fingers += 1
    if middle_tip.y < middle_pip.y:
        fingers += 1
    if ring_tip.y < ring_pip.y:
        fingers += 1
    if pinky_tip.y < pinky_pip.y:
        fingers += 1

    return fingers


model_path = ensure_model(MODEL_PATH)
base_options = python.BaseOptions(model_asset_path=str(model_path))
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.5,
)

landmarker = vision.HandLandmarker.create_from_options(options)
serial_conn = open_serial(PUERTO_SERIAL, BAUDIOS)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No hay camara rey.")

last_count = None

try:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.monotonic() * 1000)
        results = landmarker.detect_for_video(mp_image, timestamp_ms)

        finger_count = 0

        if results.hand_landmarks:
            hand_landmarks = results.hand_landmarks[0]
            handedness_label = "Right"
            if results.handedness:
                handedness_label = results.handedness[0][0].category_name

            drawing_utils.draw_landmarks(
                frame,
                hand_landmarks,
                hand_landmarker.HandLandmarksConnections.HAND_CONNECTIONS,
                drawing_styles.get_default_hand_landmarks_style(),
                drawing_styles.get_default_hand_connections_style(),
            )

            finger_count = count_fingers(hand_landmarks, handedness_label)

        cv2.putText(
            frame,
            f"Dedos: {finger_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        if finger_count != last_count:
            last_count = finger_count
            if serial_conn:
                serial_conn.write(bytes([finger_count]))

        cv2.imshow("Sesion 2 - Control Arduino", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break
finally:
    if serial_conn:
        serial_conn.close()
    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()
