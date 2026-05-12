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

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

MODEL_PATH = Path(__file__).with_name("hand_landmarker.task")

def ensure_model(path: Path) -> Path:
    if path.exists():
        return path
    try:
        urllib.request.urlretrieve(MODEL_URL, path)
    except Exception as e:
        print("Error:", e)
    return path


model_path = ensure_model(MODEL_PATH)

base_options = python.BaseOptions(model_asset_path=str(model_path))

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=6,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.5,
)

landmarker = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No hay camara rey.")

try:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # 1. Preparar imagen (Mirror y Color)
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 2. PROCESAMIENTO (MediaPipe Tasks)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.monotonic() * 1000)
        results = landmarker.detect_for_video(mp_image, timestamp_ms)

        h, w, _ = frame.shape

        # --- PASO 1: Dibujar Botón Virtual (Zona de Interés - ROI) ---
        # Dibujaremos un rectángulo que actúe como "Interruptor"
        color_boton = (0, 255, 0)  # Verde inicial
        cv2.rectangle(frame, (w - 150, 50), (w - 50, 150), color_boton, 2)
        cv2.putText(
            frame,
            "FOCO",
            (w - 140, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    hand_landmarker.HandLandmarksConnections.HAND_CONNECTIONS,
                    drawing_styles.get_default_hand_landmarks_style(),
                    drawing_styles.get_default_hand_connections_style(),
                )

                # --- PASO 2: Extraer Coordenadas del Dedo Índice ---
                # El landmark 8 es la punta del dedo índice
                indice_x = int(hand_landmarks[8].x * w)
                indice_y = int(hand_landmarks[8].y * h)

                # Dibujar un círculo en la punta del dedo para feedback visual
                cv2.circle(frame, (indice_x, indice_y), 10, (255, 0, 0), -1)

                # --- PASO 3: Lógica de Colisión (Interacción) ---
                # ¿Está el dedo dentro del cuadro del botón?
                if (w - 150 < indice_x < w - 50) and (50 < indice_y < 150):
                    color_boton = (0, 0, 255)  # Cambia a Rojo al "tocar"
                    cv2.rectangle(
                        frame,
                        (w - 150, 50),
                        (w - 50, 150),
                        color_boton,
                        -1,
                    )
                    cv2.putText(
                        frame,
                        "ON",
                        (w - 115, 110),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 255),
                        3,
                    )

        # Mostrar interfaz
        cv2.imshow("HMI Workshop - Fablab UV", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # Esc para salir
            break
finally:
    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()
