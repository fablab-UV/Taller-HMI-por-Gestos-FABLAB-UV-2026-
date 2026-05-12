#include <Servo.h>

const int LED_PIN = 3;
const int SERVO_PIN = 9;
const int BUZZER_PIN = 11;

Servo servoMotor;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  servoMotor.attach(SERVO_PIN);
  Serial.begin(9600);
}

void aplicarAccion(byte dedos) {
  int brillo = 0;
  int angulo = 0;
  bool sonar = false;

  if (dedos == 0) {
    brillo = 0;
    angulo = 0;
    sonar = false;
  } else if (dedos == 1) {
    brillo = 64;
    angulo = 45;
    sonar = false;
  } else if (dedos == 2) {
    brillo = 128;
    angulo = 90;
    sonar = false;
  } else if (dedos == 3) {
    brillo = 192;
    angulo = 135;
    sonar = false;
  } else {
    brillo = 255;
    angulo = 180;
    sonar = true;
  }

  analogWrite(LED_PIN, brillo);
  servoMotor.write(angulo);

  if (sonar) {
    tone(BUZZER_PIN, 1500, 100);
  } else {
    noTone(BUZZER_PIN);
  }
}

void loop() {
  if (Serial.available() > 0) {
    byte dedos = Serial.read();
    aplicarAccion(dedos);
  }
}
