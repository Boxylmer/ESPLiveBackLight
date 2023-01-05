#include <FastLED.h>
#define NUM_LEDS 60 //Basically set as high as possible without seeing lag
#define DATAPIN 6
#define BAUD_RATE 200000
#define STOP_BYTE 0
#define START_BYTE 1
#define DATABYTESTART 20

//incoming stream in format of {1, R, G, B, R, G, B, ... , 0}
#define RECIEVING 1
#define WAITING 0
int state = WAITING; //0 = waiting, 1 = recieving, ...
bool NEWDATA = false;
byte MESSAGE;
int ledTracker = 0; //index starts at 0
int rgbTracker = 0; //0 = red, 1 = green, 2 = blue
int rgb[] = {0,0,0};

CRGB leds[NUM_LEDS]; //put number of LEDS to run here
void setup() {
  FastLED.addLeds<WS2812B, DATAPIN, GRB>(leds, NUM_LEDS);
  Serial.begin(BAUD_RATE);
  //pinMode(LED_BUILTIN, OUTPUT);
  FastLED.clear();
  FastLED.show();  
}

void loop() {
  
  if (Serial.available()){
    MESSAGE = Serial.read();
    if (MESSAGE == 1){
      Serial.readBytes( (char*)leds, NUM_LEDS * 3);
      FastLED.show();//once we're finished recieving, show what we recieved
    }
  }
}
