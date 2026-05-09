# CV-HMI: Control Gestual mediante Visión Artificial
### Propuesta de Transferencia Tecnológica | Fablab UV

Este repositorio contiene el material técnico y didáctico para el taller intensivo de **Interfaz Hombre-Máquina (HMI)** basado en visión artificial. El proyecto está estructurado en **dos sesiones**, partiendo desde la detección de gestos en pantalla hasta el control físico de hardware real mediante Arduino.

---

# Objetivo del Taller

Desarrollar un sistema de control gestual funcional capaz de:

1. **Captura Proactiva:** Procesar video en tiempo real con latencia mínima.
2. **Detección de Landmarks:** Localizar los 21 puntos clave de la mano usando el modelo de grafos de **MediaPipe**.
3. **Lógica de Interacción:** Mapear coordenadas espaciales para activar "Botones Virtuales" (ROI - Region of Interest).
4. **Control de Hardware:** Transmitir comandos gestuales vía Serial a un Arduino para actuar sobre componentes físicos reales (LEDs, servomotores, buzzer).

---

# Requisitos del Sistema

Para asegurar compatibilidad total durante el taller, se recomienda utilizar exactamente las siguientes versiones:

* **Python:** `Python 3.11.9`
* **Hardware Sesión 1:** Webcam integrada o USB.
* **Hardware Sesión 2:** Arduino UNO/Nano, LED, resistencia 220Ω, servomotor SG90, buzzer pasivo, cables Dupont.
* **Sistema Operativo:** Windows 10/11 recomendado.

> **Importante:**  
> Versiones más recientes de Python (por ejemplo Python 3.12+) presentan incompatibilidades con algunas versiones de MediaPipe utilizadas en este taller.

---

# Instalación del Entorno

## 1. Instalar Python 3.11.9

Descargar desde:

https://www.python.org/downloads/release/python-3119/

Durante la instalación marcar:

```
☑ Add python.exe to PATH
```

## 2. Crear entorno virtual

Abrir PowerShell en la carpeta del proyecto:

```bash
py -3.11 -m venv .venv
```

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

**NO utilizar**:

```bash
pip install mediapipe
```

ya que instala versiones recientes incompatibles con la API clásica utilizada en este taller.

Instalar exactamente:

```bash
pip install mediapipe==0.10.9 opencv-python numpy pyserial
```

> `pyserial` es necesario a partir de la Sesión 2 para la comunicación con Arduino.

---

# Estructura del Repositorio

```
CV-HMI/
│
├── sesion_1/
│   ├── main.py                  ← Código final Sesión 1
│   └── starter_template.py      ← Plantilla de inicio
│
├── sesion_2/
│   ├── main_session2.py         ← Código Python Sesión 2
│   └── arduino_session2.ino     ← Código Arduino Sesión 2
│
├── requirements.txt
└── README.md
```

---

# SESIÓN 1 — Botón Virtual con Visión Artificial

## Objetivo

Construir una interfaz gestual en pantalla que detecte la posición del dedo índice y active un botón virtual al colisionar con una región de interés (ROI).

## Flujo del Sistema

1. Captura de video mediante webcam.
2. Conversión BGR → RGB.
3. Procesamiento mediante MediaPipe.
4. Extracción de landmarks.
5. Obtención de coordenadas del Landmark 8 (punta del dedo índice).
6. Verificación de colisión con ROI.
7. Activación visual del botón virtual.

## Lógica de Colisión

El sistema calcula si la posición del dedo se encuentra dentro de una región rectangular dibujada con OpenCV:

$$
(x_{min} < x_{finger} < x_{max}) \land (y_{min} < y_{finger} < y_{max})
$$

## Ejecución

```bash
python sesion_1/main.py
```

Presionar `ESC` para cerrar la ventana de OpenCV.

---

# SESIÓN 2 — Control de Hardware con Arduino

## Objetivo

Extender el sistema de la Sesión 1 para **controlar hardware real** mediante gestos de la mano. Python detecta cuántos dedos están levantados y envía un número por puerto Serial al Arduino, que actúa sobre LEDs, un servomotor y un buzzer.

## Tabla de Gestos y Acciones

| Dedos levantados | LED | Servomotor | Buzzer |
|:---:|---|---|---|
| ✊ 0 (Puño) | Apagado | 0° | Silencio |
| ☝️ 1 dedo | Brillo bajo (PWM 64) | 45° | Silencio |
| ✌️ 2 dedos | Brillo medio (PWM 128) | 90° | Silencio |
| 🤟 3 dedos | Brillo alto (PWM 192) | 135° | Silencio |
| 🖐️ 4-5 dedos | Brillo máximo (PWM 255) | 180° | Pitido |

## Diagrama de Conexión Arduino

```
Arduino UNO
├── Pin 3  (PWM) ──── LED (+) ──── Resistencia 220Ω ──── GND
├── Pin 9  (PWM) ──── Servo (señal naranja)
│                     Servo (rojo)  ──── 5V
│                     Servo (marrón) ─── GND
└── Pin 11 ──────── Buzzer (+) ──── GND
```

## Flujo del Sistema (Sesión 2)

```
Webcam → MediaPipe → Conteo de dedos → Serial USB → Arduino → Hardware físico
```

## Ejecución

**Paso 1:** Cargar el sketch en Arduino IDE:
```
sesion_2/arduino_session2.ino
```

**Paso 2:** Identificar el puerto COM del Arduino (ej: `COM3` en Windows).

**Paso 3:** Modificar en `main_session2.py` la línea:
```python
PUERTO_SERIAL = 'COM3'  # Cambiar según corresponda
```

**Paso 4:** Ejecutar:
```bash
python sesion_2/main_session2.py
```

Presionar `ESC` para cerrar.

## Consideraciones Técnicas

- La comunicación Serial opera a **9600 baudios**.
- Python envía un byte con el número de dedos detectados (`0`–`5`) cada vez que el valor cambia.
- Arduino usa la librería `Servo.h` (incluida en el IDE).
- Se recomienda alimentar el servomotor desde la salida de 5V del Arduino para movimientos cortos; para servos de mayor torque usar fuente externa.

---

# Implementación Técnica General

## Detección de Landmarks

MediaPipe detecta **21 puntos clave** por mano. En la Sesión 1 se usa solo el Landmark 8 (índice). En la Sesión 2 se comparan las posiciones Y de las puntas (landmarks 4, 8, 12, 16, 20) con sus nudillos (landmarks 3, 6, 10, 14, 18) para determinar si cada dedo está extendido.

## Algoritmo de Conteo de Dedos

```
Para cada dedo (índice al meñique):
    Si punta_y < nudillo_y → dedo LEVANTADO (+1)
    Si punta_y > nudillo_y → dedo CERRADO

Para el pulgar:
    Si punta_x > nudillo_x (mano derecha) → pulgar ABIERTO (+1)
```

---

# Tecnologías Utilizadas

* Python 3.11
* OpenCV
* MediaPipe
* NumPy
* PySerial
* Arduino (C/C++)
* Visión Artificial
* Procesamiento en Tiempo Real
* Interfaces HMI
* Comunicación Serial

---

# Aplicaciones Potenciales

* Interfaces médicas sin contacto
* Automatización industrial
* Control gestual de robótica
* Sistemas interactivos y domótica
* Accesibilidad para personas con movilidad reducida
* Entornos con riesgo de contaminación (quirófanos, laboratorios)

---

# Metodología (ABP)

El taller utiliza **Aprendizaje Basado en Problemas (ABP)**, desafiando a los estudiantes a resolver la operatividad de interfaces en entornos donde el contacto físico es riesgoso o imposible, por ejemplo:

* Quirófanos
* Talleres mecánicos
* Laboratorios
* Manipulación de sustancias peligrosas

---

# Resultados Esperados

Al finalizar ambas sesiones, el estudiante será capaz de:

* Capturar y procesar video en tiempo real.
* Utilizar modelos de visión artificial para detección de gestos.
* Detectar y contar dedos a partir de landmarks de mano.
* Implementar regiones de interacción virtual (ROI).
* Establecer comunicación Serial entre Python y Arduino.
* Controlar hardware físico (LED, servo, buzzer) mediante gestos.
* Comprender el flujo completo de un sistema HMI basado en visión computacional.

---

# Créditos

Proyecto desarrollado por:

* Maria-Ignacia Rojas
* Maximiliano Gaete

**Estudiantes de Pregrado**  
Carrera de Ingeniería Civil Biomédica  
Universidad de Valparaíso

---

Desarrollado para el **Fablab de la Universidad de Valparaíso**
