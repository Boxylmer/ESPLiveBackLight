#define FASTLED_ESP8266_NODEMCU_PIN_ORDER
#include <FastLED.h>
#define NUM_LEDS 120 //Basically set as high as possible without seeing lag
#define DATAPIN 2 //6
#define BAUD_RATE 115200 // 200000
#define STOP_BYTE 255
#define START_BYTE 55

#define STATE_FILL_BUFFER 1 
#define STATE_IDLE 2

#define RED 0
#define BLUE 1
#define GREEN 2


//incoming stream in format of {1, R, G, B, R, G, B, ... , 0}
byte MESSAGE;
byte CURRENTBYTE;
byte STATE;

int LEDCOUNT;
int CURRENTCOLOR;

CRGB leds[NUM_LEDS]; //put number of LEDS to run here
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  FastLED.addLeds<WS2812B, DATAPIN, GRB>(leds, NUM_LEDS);
  Serial.setRxBufferSize(10240); // We acquire data
  Serial.begin(BAUD_RATE);
  FastLED.clear();
  leds[0] = CRGB::Red;
  leds[1] = CRGB::Blue;
  leds[2] = CRGB::Green;
  FastLED.show();  

  idlestate();
}

// // Will's method, very naieve: errors just for fun and only when people aren't watching my stream
// void loop() {
//   if (Serial.available()){
//     MESSAGE = Serial.read();
//     if (MESSAGE == START_BYTE){
//       digitalWrite(LED_BUILTIN, HIGH);
//       // Serial.readBytes((char*)leds, NUM_LEDS * 3);
//       Serial.readBytesUntil(END_TOKEN, (char*)leds, NUM_LEDS * 3);
//       FastLED.show();//once we're finished recieving, show what we recieved
//       digitalWrite(LED_BUILTIN, LOW);
//     }
//   }
// }

// void loop() {
//   if (Serial.available()){
//     CURRENTBYTE = Serial.read();
//     if(STATE == STATE_FILL_BUFFER){
//       digitalWrite(LED_BUILTIN, LOW);
//       if(CURRENTBYTE == STOP_BYTE){
//         idlestate();
//         FastLED.show();
//         return;
//       }
//       if(LEDCOUNT >= NUM_LEDS){
//         // we should never reach this case unless something has been missed
//         idlestate();
//         return;
//       }
//       if (CURRENTCOLOR == RED){
//         leds[LEDCOUNT].red = CURRENTBYTE;
//         CURRENTCOLOR = GREEN;
//       }else if(CURRENTCOLOR == GREEN){
//         leds[LEDCOUNT].green = CURRENTBYTE;
//         CURRENTCOLOR = BLUE;
//       }else if(CURRENTCOLOR == BLUE){
//         leds[LEDCOUNT].blue = CURRENTBYTE;
//         CURRENTCOLOR = RED;
//         LEDCOUNT += 1;
//       }
//     }else if(STATE == STATE_IDLE){
//       digitalWrite(LED_BUILTIN, HIGH);
//       if (CURRENTBYTE == START_BYTE){
//         fillbufferstate();
//       }
//     }
//   }
// }

void idlestate(){
  STATE = STATE_IDLE;
  LEDCOUNT = 0;
  CURRENTCOLOR = RED;
}
void fillbufferstate(){
  STATE = STATE_FILL_BUFFER;
  LEDCOUNT = 0;
  CURRENTCOLOR = RED;
}


// MaderDash method, add in an entire string at once and parse.
void loop() { // [1, r, g, b, r, g, b, \n]

  if (Serial.available()){
    digitalWrite(LED_BUILTIN, LOW);
    String msg = Serial.readStringUntil('\n'); // will include newline chars
    for(int i = 0; i < NUM_LEDS * 3; i+=3){
      leds[i / 3].r = msg[i + 1];
      leds[i / 3].g = msg[i + 2];
      leds[i / 3].b = msg[i + 3];
    }
    FastLED.show();
    digitalWrite(LED_BUILTIN, HIGH);
  }
}

