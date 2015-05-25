#include <Servo.h>

Servo myservo;  // create servo object to control a servo

// range in which servo moves
int sMin = 65;
int sMax = 83;

void setup()
{
  myservo.attach(13);
  myservo.write(sMin);
  Serial.begin(9600);
}

void doSwitch() {
  myservo.write(sMax);
  delay(300);
  myservo.write(sMin);
  Serial.println("switched");
}

int readNumber() {
  return Serial.parseInt();
}

void showVals() {
  Serial.print("min: ");
  Serial.println(sMin);
  Serial.print("max: ");
  Serial.println(sMax);
}

void waitForCommand() {
  while (true) {
   while (Serial.available() == 0) {
     delay(20);
   }
   int read = Serial.read();
   if (read=='c') {
     return;
   }
   else if (read == 'v') {
     Serial.read(); // read space;
     while (Serial.available() == 0) { delay(20); }
     sMin = readNumber();
     sMax = readNumber();
     Serial.println("set new values to:");
     showVals();
     myservo.write(sMin);
     delay(100);
   }
   else if (read == 'h') {
     Serial.println("send a 'c' to trigger a press");
     Serial.println("send v [minVal] [maxVal] to change range");
     Serial.println(" eg: v 50 60");
     Serial.println("current range:");
     showVals();
   }
  } 
}

void loop() 
{ 
  waitForCommand();
  doSwitch();
} 

