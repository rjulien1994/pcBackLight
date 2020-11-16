#include <Adafruit_NeoPixel.h>
#define PIN 6

const byte ledR[2] = {14,7};
const byte totalLed = 2*(ledR[0]+ledR[1]);

Adafruit_NeoPixel strip = Adafruit_NeoPixel(totalLed, PIN, NEO_GRB + NEO_KHZ800);

byte data[totalLed*3];
byte dataload[] = {30,30,30,36};

unsigned long timer;

void setup() 
{
  Serial.begin(250000);
  delay(150);
  strip.begin();
  strip.show();
}

void loop() 
{
  dataRetrieve();

  colorDisplay();
}

void dataRetrieve()
{
  byte dataReceived = 0;
  for(byte package = 1; package < sizeof(dataload) + 1; package++)
  {
    Serial.write(package);
    byte byteInput = dataload[package - 1];

    timer = millis();
  
    while(Serial.available() < byteInput)
    {
      delay(1);
      if(millis()- timer > 1000)
      {
        for(byte i = 0; i < totalLed; i++)
        {
          strip.setPixelColor(i, 0, 0, 0);
        }
        strip.show();

        delay(2000);

        Serial.write(package);
        timer = millis();
      }
    }

    for(byte i = 0; i < byteInput; i++)
    {
      data[dataReceived + i] = Serial.read();
    }
    dataReceived = dataReceived + byteInput;
  }
  Serial.write(sizeof(dataload) + 1);
  
  delay(1);
}

void colorDisplay()
{
  for(byte i = 0; i < totalLed; i++)
  {
    strip.setPixelColor(i, data[3*i]/2, data[3*i+1]/2, data[3*i+2]/2);
  }
  strip.show();
}
