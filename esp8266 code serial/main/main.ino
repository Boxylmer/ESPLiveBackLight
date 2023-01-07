#define FASTLED_ESP8266_NODEMCU_PIN_ORDER
#include <FastLED.h>
#define NUM_LEDS 10 //Basically set as high as possible without seeing lag
#define DATAPIN 2 //6
#define BAUD_RATE 200000 // 200000
#define STOP_BYTE 0
#define START_BYTE 1


//incoming stream in format of {1, R, G, B, R, G, B, ... , 0}
byte MESSAGE;


CRGB leds[NUM_LEDS]; //put number of LEDS to run here
void setup() {
  // pinMode(LED_BUILTIN, OUTPUT);
  FastLED.addLeds<WS2812B, DATAPIN, GRB>(leds, NUM_LEDS);
  Serial.begin(BAUD_RATE);
  //pinMode(LED_BUILTIN, OUTPUT);
  FastLED.clear();
  leds[0] = CRGB::Red;
  leds[1] = CRGB::Blue;
  leds[2] = CRGB::Green;
  FastLED.show();  
}

void loop() {
  if (Serial.available()){
    MESSAGE = Serial.read();
    if (MESSAGE == START_BYTE){
      // digitalWrite(LED_BUILTIN, HIGH);
      Serial.readBytes((char*)leds, NUM_LEDS * 3);
      FastLED.show();//once we're finished recieving, show what we recieved
      // digitalWrite(LED_BUILTIN, LOW);
    }
  }
}
