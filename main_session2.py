import cv2
import mediapipe as mp
import numpy as np
import serial
import time

# =============================================================
# CV-HMI | SESIÓN 2 - Control Gestual + Arduino
# Fablab UV | Ingeniería Civil Biomédica - Universidad de Valparaíso
# =============================================================

# --- CONFIGURACIÓN SERIAL ---
# Cambiar 'COM3' por el puerto correspondiente a tu Arduino
# Windows: 'COM3', 'COM4', etc.  |  Linux/Mac: '/dev/ttyUSB0'
PUERTO_SERIAL = 'COM3'
BAUDRATE = 9600

# --- INICIALIZAR SERIAL ---
arduino = None
try:
    arduino = serial.Serial(PUERTO_SERIAL, BAUDRATE, timeout=1)
    time.sleep(2)  # Esperar a que Arduino reinicie
    print(f"[OK] Arduino conectado en {PUERTO_SERIAL}")
except Exception as e:
    print(f"[AVISO] No se pudo conectar al Arduino: {e}")
    print("[AVISO] El programa correrá en modo solo-visualización.")

# --- CONFIGURACIÓN MEDIAPIPE ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)

# --- INDICES DE LANDMARKS ---
# Puntas de los dedos: pulgar, índice, medio, anular, meñique
TIPS = [4, 8, 12, 16, 20]
# Nudillos de referencia (segunda falange)
KNUCKLES = [3, 6, 10, 14, 18]

# --- COLORES ---
COLOR_VERDE   = (0, 220, 100)
COLOR_AZUL    = (255, 140, 0)
COLOR_ROJO    = (0, 60, 255)
COLOR_BLANCO  = (255, 255, 255)
COLOR_GRIS    = (60, 60, 60)
COLOR_AMARILLO = (0, 220, 220)

# --- ESTADO PREVIO (para enviar solo cuando cambia) ---
dedos_previo = -1

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("[INFO] Iniciando captura. Presiona ESC para salir.")


def contar_dedos(landmarks, w, h):
    """
    Cuenta cuántos dedos están levantados.
    Compara la posición Y de la punta con el nudillo de referencia.
    Para el pulgar compara en X (mano derecha).
    Retorna un entero entre 0 y 5.
    """
    dedos = 0

    # --- Pulgar (comparación horizontal) ---
    pulgar_punta_x = landmarks[TIPS[0]].x * w
    pulgar_nudillo_x = landmarks[KNUCKLES[0]].x * w
    if pulgar_punta_x > pulgar_nudillo_x:
        dedos += 1

    # --- Resto de dedos (comparación vertical) ---
    for i in range(1, 5):
        punta_y   = landmarks[TIPS[i]].y * h
        nudillo_y = landmarks[KNUCKLES[i]].y * h
        if punta_y < nudillo_y:
            dedos += 1

    return dedos


def dibujar_panel(frame, dedos, w, h):
    """Dibuja el panel de información y la barra de nivel."""

    # --- Panel lateral oscuro ---
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (220, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    # --- Título ---
    cv2.putText(frame, "CV-HMI", (15, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_VERDE, 2)
    cv2.putText(frame, "Fablab UV", (15, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_GRIS, 1)
    cv2.line(frame, (15, 75), (205, 75), COLOR_GRIS, 1)

    # --- Dedos detectados ---
    cv2.putText(frame, "Dedos:", (15, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_BLANCO, 1)
    cv2.putText(frame, str(dedos), (15, 165),
                cv2.FONT_HERSHEY_SIMPLEX, 2.5, COLOR_AMARILLO, 4)

    # --- Barra de nivel ---
    cv2.putText(frame, "Nivel", (15, 210),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_GRIS, 1)
    barra_max_h = 200
    barra_y0 = 220
    barra_x = 30
    barra_w = 40
    cv2.rectangle(frame, (barra_x, barra_y0),
                  (barra_x + barra_w, barra_y0 + barra_max_h), COLOR_GRIS, 1)
    nivel = int((dedos / 5) * barra_max_h)
    if nivel > 0:
        cv2.rectangle(frame,
                      (barra_x, barra_y0 + barra_max_h - nivel),
                      (barra_x + barra_w, barra_y0 + barra_max_h),
                      COLOR_VERDE, -1)

    # --- Estado hardware ---
    cv2.line(frame, (15, 440), (205, 440), COLOR_GRIS, 1)
    etiquetas = [
        ("LED",    f"PWM: {min(dedos * 51, 255)}"),
        ("SERVO",  f"{dedos * 36}°"),
        ("BUZZER", "ON" if dedos >= 5 else "OFF"),
    ]
    colores_estado = [COLOR_AMARILLO, COLOR_AZUL, COLOR_ROJO if dedos >= 5 else COLOR_GRIS]
    for i, (nombre, valor) in enumerate(etiquetas):
        y = 465 + i * 45
        cv2.putText(frame, nombre, (15, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_GRIS, 1)
        cv2.putText(frame, valor, (15, y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, colores_estado[i], 2)

    # --- Estado conexión ---
    estado_txt = "Serial: OK" if arduino and arduino.is_open else "Serial: OFF"
    estado_color = COLOR_VERDE if arduino and arduino.is_open else COLOR_ROJO
    cv2.putText(frame, estado_txt, (15, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, estado_color, 1)


# ==================== LOOP PRINCIPAL ====================
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    dedos_detectados = 0

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Dibujar landmarks
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=COLOR_VERDE, thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=COLOR_AZUL, thickness=2)
            )

            # Contar dedos
            dedos_detectados = contar_dedos(hand_landmarks.landmark, w, h)

            # Marcar punta del índice
            ix = int(hand_landmarks.landmark[8].x * w)
            iy = int(hand_landmarks.landmark[8].y * h)
            cv2.circle(frame, (ix, iy), 12, COLOR_AMARILLO, -1)
            cv2.circle(frame, (ix, iy), 14, COLOR_BLANCO, 2)

    # --- Enviar a Arduino solo si cambió el valor ---
    if dedos_detectados != dedos_previo:
        if arduino and arduino.is_open:
            try:
                arduino.write(bytes([dedos_detectados]))
            except Exception as e:
                print(f"[ERROR Serial] {e}")
        dedos_previo = dedos_detectados

    # --- Dibujar interfaz ---
    dibujar_panel(frame, dedos_detectados, w, h)

    cv2.imshow('CV-HMI Sesion 2 | Fablab UV', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
        break

# --- LIMPIEZA ---
cap.release()
cv2.destroyAllWindows()
hands.close()
if arduino and arduino.is_open:
    arduino.close()
    print("[INFO] Conexión Serial cerrada.")
print("[INFO] Programa finalizado.")
