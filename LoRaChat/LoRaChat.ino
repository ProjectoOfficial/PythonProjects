#include <SoftwareSerial.h>

#define ADDRESS 15
#define COMMAND_DELAY 100
SoftwareSerial mySerial(3, 2); // RX, TX

void setup() {
  Serial.begin(115200);
  while (!Serial);
  mySerial.begin(115200);

  String command = "AT+BAND=470000000\r\n";
  mySerial.write(command.c_str());
  delay(COMMAND_DELAY);

  command = "AT+ADDRESS=" + String(ADDRESS) + "\r\n";
  mySerial.write(command.c_str());
  delay(COMMAND_DELAY);
}

void loop() {
  if (mySerial.available()) {
    Serial.write(mySerial.read());
  }

  if (Serial.available()) {
    mySerial.write(Serial.read());
  }
}
