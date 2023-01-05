#include <ESP8266WiFi.h>
// #include "ESPAsyncWebServer.h"
#include <ESP8266WebServer.h>


// Replace with your network credentials
const char* ssid     = "Thermal Masturbation Camera 1";
const char* password = "memetown";

// Set web server port number to 80
ESP8266WebServer  server(80);

// // Variable to store the HTTP request
// String header;


void setup() {
  // Connect to Wi-Fi network with SSID and password
  Serial.begin(115200);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  server.on("/test", function);
  server.on("/postplain/", HTTP_POST, handlePlain);
  // server.on("/postform/", handleForm);
  server.onNotFound(handleNotFound);
  server.begin();
  
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient(); //this is required for handling the incoming requests
}

void function() {
  //do something
  // String varname = server.arg("abc"); //this lets you access the value using the key as you have set in your json for ex:

  // json={'body':'foo'}
  // so you can access the value of body by using server.arg('body');
}

void handlePlain() {
  if (server.method() != HTTP_POST) {
    // digitalWrite(led, 1);
    server.send(405, "text/plain", "Method Not Allowed");
    // digitalWrite(led, 0);
  } else {
    // digitalWrite(led, 1);
    server.send(200, "text/plain", "POST body was:\n" + server.arg("plain"));
    // digitalWrite(led, 0);
  }
}

void handleNotFound() {
  // digitalWrite(led, 1);
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++) { message += " " + server.argName(i) + ": " + server.arg(i) + "\n"; }
  server.send(404, "text/plain", message);
  // digitalWrite(led, 0);
}
