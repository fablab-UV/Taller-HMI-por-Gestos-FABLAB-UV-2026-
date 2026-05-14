# CV-HMI: Control Gestual mediante Visión Artificial
### Propuesta de Transferencia Tecnológica | Fablab UV

Este repositorio contiene el material técnico y didáctico para el taller intensivo de **Interfaz Hombre-Máquina (HMI)** basado en visión artificial. El proyecto está diseñado para ser implementado en una sesión de 90 minutos, transformando una cámara web en un sensor de control sin contacto.

---

# Objetivo del Taller

Desarrollar un sistema de control gestual funcional capaz de:

1. **Captura Proactiva:** Procesar video en tiempo real con latencia mínima.
2. **Detección de Landmarks:** Localizar los 21 puntos clave de la mano usando el modelo de grafos de **MediaPipe**.
3. **Lógica de Interacción:** Mapear coordenadas espaciales para activar "Botones Virtuales" (ROI - Region of Interest).

---

# Requisitos del Sistema

Para asegurar compatibilidad durante el taller, se recomienda:

* **Python:** 3.10+ (64-bit)
* **Hardware:** Webcam integrada o USB.
* **Sistema Operativo:** Windows 10/11 recomendado.

---

# Instalación del Entorno

## 1. Instalar Python 3.10+

Descargar desde:

https://www.python.org/downloads/

Durante la instalación marcar:

```text
☑ Add python.exe to PATH
```
---

## 2. Crear entorno virtual

Abrir PowerShell en la carpeta del proyecto:

```bash
py -3 -m venv .venv
```

---

## 3. Activar entorno virtual

### Windows PowerShell

```bash
.venv\Scripts\activate
```

Si el entorno se activó correctamente, la terminal mostrará:

```bash
(.venv)
```

---

# Instalación de Librerías

Instalar:

```bash
pip install mediapipe opencv-python numpy ffpyplayer pyserial
```

Nota: En la primera ejecucion, el modelo de mano se descarga automaticamente.

---

# Ejecución del Proyecto

## Sesión 1 — Interfaz gestual con botón virtual

Ejecutar:

```bash
python main.py
```

Presionar:

```text
ESC
```

para cerrar la ventana de OpenCV.

## Sesión 2 — Control de Hardware con Arduino

Objetivo: Extender el sistema de la Sesión 1 para controlar hardware real mediante gestos de la mano. Python detecta cuántos dedos están levantados y envía un número por puerto Serial al Arduino, que actúa sobre LEDs, un servomotor y un buzzer.

### Tabla de Gestos y Acciones

| Dedos levantados | LED | Servomotor | Buzzer |
| --- | --- | --- | --- |
| ✊ 0 (Puño) | Apagado | 0° | Silencio |
| ☝️ 1 dedo | Brillo bajo (PWM 64) | 45° | Silencio |
| ✌️ 2 dedos | Brillo medio (PWM 128) | 90° | Silencio |
| 🤟 3 dedos | Brillo alto (PWM 192) | 135° | Silencio |
| 🖐️ 4-5 dedos | Brillo máximo (PWM 255) | 180° | Pitido |

### Conexiones Arduino (UNO)

```
Arduino UNO
├── Pin 3  (PWM) ──── LED (+) ──── Resistencia 220Ω ──── GND
├── Pin 9  (PWM) ──── Servo (señal naranja)
│                     Servo (rojo)  ──── 5V
│                     Servo (marrón) ─── GND
└── Pin 11 ──────── Buzzer (+) ──── GND
```
# Diagrama de conexiones al Arduino (UNO)

![Circuito Arduino](https://github.com/user-attachments/assets/2a57040c-fbfa-4f97-8d42-27e9b3d7845a)

### Flujo del Sistema (Sesión 2)

Webcam → MediaPipe → Conteo de dedos → Serial USB → Arduino → Hardware físico

### Ejecución

Paso 1: Cargar el sketch en Arduino IDE:

```text
sesion_2/arduino_session2.ino
```

Paso 2: Identificar el puerto COM del Arduino (ej: COM3 en Windows).

Paso 3: Modificar en el script:

```text
PUERTO_SERIAL = "COM3"  # Cambiar según corresponda
```

Paso 4: Ejecutar:

```bash
python sesion_2/main_session2.py
```

Presionar ESC para cerrar.

### Consideraciones Técnicas

- La comunicación Serial opera a 9600 baudios.
- Python envía un byte con el número de dedos detectados (0–5) cada vez que el valor cambia.
- Arduino usa la librería Servo.h (incluida en el IDE).
- Se recomienda alimentar el servomotor desde la salida de 5V del Arduino para movimientos cortos; para servos de mayor torque usar fuente externa.

---

# Estructura del Repositorio

```text
CV-HMI/
│
├── face_landmarker.task
├── hand_landmarker.task
├── main.py
├── README.md
├── sesion_2/
│   ├── arduino_session2.ino
│   └── main_session2.py
└── tlabaja.py
```

### Archivos

* `main.py`  
  Código final con detección de mano, interacción y feedback visual (Sesión 1).

* `sesion_2/main_session2.py`  
  Script de conteo de dedos y envío por Serial a Arduino.

* `sesion_2/arduino_session2.ino`  
  Sketch para controlar LED, servo y buzzer.

---

# Implementación Técnica

El flujo de trabajo se centra en la detección del **Landmark 8** (punta del dedo índice).

El sistema calcula si la posición del dedo se encuentra dentro de una región rectangular dibujada mediante OpenCV:

$$
(x_{min} < x_{finger} < x_{max}) \land (y_{min} < y_{finger} < y_{max})
$$

Cuando esta condición se cumple, el sistema activa un evento visual que simula el accionamiento de un actuador físico.

---

# Flujo del Sistema

1. Captura de video mediante webcam.
2. Conversión BGR → RGB.
3. Procesamiento mediante MediaPipe.
4. Extracción de landmarks.
5. Obtención de coordenadas del dedo índice.
6. Verificación de colisión con ROI.
7. Activación visual del botón virtual.

---

# Tecnologías Utilizadas

* Python
* OpenCV
* MediaPipe
* NumPy
* Visión Artificial
* Procesamiento en Tiempo Real
* Interfaces HMI

---

# Aplicaciones Potenciales

* Interfaces médicas sin contacto
* Automatización industrial
* Control gestual
* Sistemas interactivos
* Robótica
* Accesibilidad
* Domótica

---

# Metodología (ABP)

El taller utiliza **Aprendizaje Basado en Problemas (ABP)**, desafiando a los estudiantes a resolver la operatividad de interfaces en entornos donde el contacto físico es riesgoso o imposible, por ejemplo:

* Quirófanos
* Talleres mecánicos
* Laboratorios
* Manipulación de sustancias peligrosas

---

# Resultados Esperados

Al finalizar el taller, el estudiante será capaz de:

* Capturar video en tiempo real.
* Utilizar modelos de visión artificial.
* Detectar landmarks de mano.
* Implementar regiones de interacción.
* Construir interfaces gestuales funcionales.
* Comprender principios básicos de HMI basados en visión computacional.

---

# Créditos

Desarrollado por **Maximiliano Gaete** y **María Ignacia Rojas**,  
estudiantes de pregrado de Ingeniería Civil Biomédica.

Proyecto desarrollado para el **Fablab de la Universidad de Valparaíso**  
*Módulo: Visión Artificial Aplicada*
