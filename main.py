import cv2
import mediapipe as mp
import numpy as np

# --- CONFIGURACIÓN INICIAL ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    # 1. Preparar imagen (Mirror y Color)
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 2. PROCESAMIENTO (MediaPipe)
    results = hands.process(rgb_frame)
    
    h, w, _ = frame.shape

    # --- PASO 1: Dibujar Botón Virtual (Zona de Interés - ROI) ---
    # Dibujaremos un rectángulo que actúe como "Interruptor"
    color_boton = (0, 255, 0) # Verde inicial
    cv2.rectangle(frame, (w-150, 50), (w-50, 150), color_boton, 2)
    cv2.putText(frame, "FOCO", (w-140, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Dibujar los puntos clave (Landmarks)
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # --- PASO 2: Extraer Coordenadas del Dedo Índice ---
            # El landmark 8 es la punta del dedo índice
            indice_x = int(hand_landmarks.landmark[8].x * w)
            indice_y = int(hand_landmarks.landmark[8].y * h)
            
            # Dibujar un círculo en la punta del dedo para feedback visual
            cv2.circle(frame, (indice_x, indice_y), 10, (255, 0, 0), -1)

            # --- PASO 3: Lógica de Colisión (Interacción) ---
            # ¿Está el dedo dentro del cuadro del botón?
            if (w-150 < indice_x < w-50) and (50 < indice_y < 150):
                color_boton = (0, 0, 255) # Cambia a Rojo al "tocar"
                cv2.rectangle(frame, (w-150, 50), (w-50, 150), color_boton, -1) # Rellenar
                cv2.putText(frame, "ON", (w-115, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

    # Mostrar interfaz
    cv2.imshow('HMI Workshop - Fablab UV', frame)

    if cv2.waitKey(1) & 0xFF == 27: # Esc para salir
        break

cap.release()
cv2.destroyAllWindows()
