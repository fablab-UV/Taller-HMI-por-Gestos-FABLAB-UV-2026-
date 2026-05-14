import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

from pathlib import Path
import time
import urllib.request
import serial

# Drawing utilities
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

# Modelo MediaPipe
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

MODEL_PATH = Path(__file__).resolve().parent / "hand_landmarker.task"

# Arduino
PUERTO_SERIAL = "COM9" # Cambiar por el correcto
BAUDIOS = 9600


def ensure_model(path: Path) -> Path:

    if path.exists():
        return path

    print("Descargando modelo...")

    try:
        urllib.request.urlretrieve(MODEL_URL, path)
        print("Modelo descargado correctamente.")

    except Exception as e:
        print("Error descargando modelo:", e)

    return path


def open_serial(port: str, baudrate: int):

    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        print("Arduino conectado.")
        return ser

    except Exception as e:
        print("No se pudo abrir el puerto serial:", e)
        return None


def count_fingers(landmarks, handedness_label: str):

    fingers = 0

    # Pulgar
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]

    if handedness_label == "Right":
        if thumb_tip.x > thumb_ip.x:
            fingers += 1
    else:
        if thumb_tip.x < thumb_ip.x:
            fingers += 1

    # Índice
    if landmarks[8].y < landmarks[6].y:
        fingers += 1

    # Medio
    if landmarks[12].y < landmarks[10].y:
        fingers += 1

    # Anular
    if landmarks[16].y < landmarks[14].y:
        fingers += 1

    # Meñique
    if landmarks[20].y < landmarks[18].y:
        fingers += 1

    return fingers


# Descargar modelo si no existe
model_path = ensure_model(MODEL_PATH)

# Configuración MediaPipe
base_options = python.BaseOptions(
    model_asset_path=str(model_path)
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.5,
)

# Crear detector
landmarker = vision.HandLandmarker.create_from_options(options)

# Conectar Arduino
serial_conn = open_serial(PUERTO_SERIAL, BAUDIOS)

# Abrir cámara
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara.")

last_count = -1

try:

    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            break

        # Efecto espejo
        frame = cv2.flip(frame, 1)

        # Convertir a RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Crear imagen MediaPipe
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp_ms = int(time.monotonic() * 1000)

        # Detectar mano
        results = landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        finger_count = 0

        # Si encuentra mano
        if results.hand_landmarks:

            hand_landmarks = results.hand_landmarks[0]

            handedness_label = "Right"

            if results.handedness:
                handedness_label = (
                    results.handedness[0][0].category_name
                )

            # Convertir landmarks al formato antiguo
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()

            hand_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z
                )
                for landmark in hand_landmarks
            ])

            # Dibujar landmarks
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks_proto,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style(),
            )

            # Contar dedos
            finger_count = count_fingers(
                hand_landmarks,
                handedness_label
            )

        # Mostrar texto
        cv2.putText(
            frame,
            f"Dedos: {finger_count}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # Enviar al Arduino si cambia
        if finger_count != last_count:

            last_count = finger_count

            if serial_conn:
                serial_conn.write(bytes([finger_count]))

        # Mostrar ventana
        cv2.imshow("Sesion 2 - Control Arduino", frame)

        # ESC para salir
        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:

    if serial_conn:
        serial_conn.close()

    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()
