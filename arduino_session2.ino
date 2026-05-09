/*
 * CV-HMI | SESIÓN 2 - Control Gestual + Arduino
 * Fablab UV | Ingeniería Civil Biomédica - Universidad de Valparaíso
 *
 * Recibe por Serial un byte con el número de dedos detectados (0-5)
 * y actúa sobre LED (PWM), Servomotor y Buzzer.
 *
 * CONEXIONES:
 *   Pin 3  → LED (+) → Resistencia 220Ω → GND
 *   Pin 9  → Servo (señal)  |  5V → Servo (VCC)  |  GND → Servo (GND)
 *   Pin 11 → Buzzer (+) → GND
 */

#include <Servo.h>

// --- PINES ---
const int PIN_LED   = 3;   // PWM
const int PIN_SERVO = 9;   // PWM
const int PIN_BUZZ  = 11;

// --- OBJETOS ---
Servo miServo;

// --- VARIABLES ---
int dedos = 0;
int dedos_previo = -1;

void setup() {
  Serial.begin(9600);

  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZ, OUTPUT);

  miServo.attach(PIN_SERVO);
  miServo.write(0);  // Posición inicial

  analogWrite(PIN_LED, 0);
  digitalWrite(PIN_BUZZ, LOW);

  Serial.println("Arduino listo. Esperando datos...");
}

void loop() {
  // --- Leer Serial ---
  if (Serial.available() > 0) {
    dedos = Serial.read();  // Leer 1 byte (0-5)

    // Ignorar valores fuera de rango
    if (dedos < 0 || dedos > 5) return;

    // Actuar solo si cambió el valor
    if (dedos != dedos_previo) {
      actualizarHardware(dedos);
      dedos_previo = dedos;

      // Feedback por Serial Monitor
      Serial.print("Dedos: ");
      Serial.print(dedos);
      Serial.print(" | LED PWM: ");
      Serial.print(mapearLED(dedos));
      Serial.print(" | Servo: ");
      Serial.print(mapearServo(dedos));
      Serial.println("°");
    }
  }
}

// --- FUNCIONES ---

int mapearLED(int d) {
  // 0 dedos = apagado, 5 dedos = máximo brillo
  return map(d, 0, 5, 0, 255);
}

int mapearServo(int d) {
  // 0 dedos = 0°, 5 dedos = 180°
  return map(d, 0, 5, 0, 180);
}

void actualizarHardware(int d) {
  // --- LED con brillo proporcional (PWM) ---
  analogWrite(PIN_LED, mapearLED(d));

  // --- Servomotor ---
  miServo.write(mapearServo(d));

  // --- Buzzer: solo activo con 5 dedos (mano abierta) ---
  if (d >= 5) {
    // Pitido corto de confirmación
    tone(PIN_BUZZ, 1000, 150);  // 1000 Hz, 150 ms
  } else {
    noTone(PIN_BUZZ);
  }
}
