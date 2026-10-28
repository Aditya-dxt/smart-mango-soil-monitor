/*
 * Mango orchard soil node - ESP32
 * Sensors : capacitive soil-moisture v1.2 (analog), DHT22 (air temp / humidity),
 *           optional DS18B20 soil temperature
 * Actuator: relay -> 12 V solenoid valve (opened by MQTT command, hard time limit)
 * Link    : Wi-Fi + MQTT (PubSubClient). Topics:
 *             orchard/<ZONE>/telemetry  (publish, JSON)
 *             orchard/<ZONE>/cmd        (subscribe, {"minutes":N})
 *
 * Libraries (Arduino Library Manager): PubSubClient, ArduinoJson, DHT sensor library,
 *             Adafruit Unified Sensor, OneWire + DallasTemperature (optional)
 *
 * NOTE: written for the ESP32 Arduino core 2.x/3.x but not hardware-tested by the
 * author of this package. Calibrate AIR_RAW / WATER_RAW and the VWC curve first.
 */
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ---------- user configuration ----------
const char* WIFI_SSID   = "YOUR_WIFI";
const char* WIFI_PASS   = "YOUR_PASSWORD";
const char* MQTT_HOST   = "192.168.1.10";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER   = "";           // leave empty if broker allows anonymous
const char* MQTT_PASS   = "";
const char* NODE_ID     = "node-01";
const char* ZONE        = "zone1";

#define PIN_SOIL   34   // ADC1 channel (ADC2 is unusable while Wi-Fi is on)
#define PIN_DHT    27
#define PIN_RELAY  26   // HIGH = valve open (set RELAY_ACTIVE_LOW if your module is inverted)
#define PIN_BATT   35   // via 100k/100k divider
const bool RELAY_ACTIVE_LOW = false;

// Two-point calibration of the capacitive probe (raw ADC 0-4095).
// AIR_RAW  = probe in dry air (0 % VWC), WATER_RAW = probe in saturated soil (~42 % VWC).
// Measure in YOUR soil; the defaults are only typical values.
const int   AIR_RAW   = 3100;
const int   WATER_RAW = 1400;
const float VWC_AT_SATURATION = 42.0;

const uint32_t SAMPLE_PERIOD_S = 900;     // 15 min
const uint32_t MAX_VALVE_MIN   = 240;     // firmware-level hard cap (backend also caps)
const uint8_t  SAMPLES = 16;              // oversampling for ADC noise

DHT dht(PIN_DHT, DHT22);
WiFiClient net;
PubSubClient mqtt(net);

volatile uint32_t valveCloseAtMs = 0;
bool valveOpen = false;

String topicTelemetry() { return String("orchard/") + ZONE + "/telemetry"; }
String topicCmd()       { return String("orchard/") + ZONE + "/cmd"; }

void setValve(bool open) {
  valveOpen = open;
  digitalWrite(PIN_RELAY, (open ^ RELAY_ACTIVE_LOW) ? HIGH : LOW);
}

void onMessage(char* topic, byte* payload, unsigned int len) {
  StaticJsonDocument<128> doc;
  if (deserializeJson(doc, payload, len)) return;
  uint32_t minutes = doc["minutes"] | 0;
  if (minutes == 0) { setValve(false); valveCloseAtMs = 0; return; }
  if (minutes > MAX_VALVE_MIN) minutes = MAX_VALVE_MIN;
  valveCloseAtMs = millis() + minutes * 60000UL;
  setValve(true);
}

void wifiConnect() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  for (int i = 0; i < 60 && WiFi.status() != WL_CONNECTED; i++) delay(500);
}

bool mqttConnect() {
  if (mqtt.connected()) return true;
  String cid = String("mango-") + NODE_ID;
  bool ok = strlen(MQTT_USER) ? mqtt.connect(cid.c_str(), MQTT_USER, MQTT_PASS)
                              : mqtt.connect(cid.c_str());
  if (ok) mqtt.subscribe(topicCmd().c_str(), 1);
  return ok;
}

float readSoilVwc() {
  uint32_t acc = 0;
  for (uint8_t i = 0; i < SAMPLES; i++) { acc += analogRead(PIN_SOIL); delay(5); }
  float raw = acc / (float)SAMPLES;
  float frac = (AIR_RAW - raw) / float(AIR_RAW - WATER_RAW);   // 0 = dry, 1 = saturated
  frac = constrain(frac, 0.0f, 1.0f);
  return frac * VWC_AT_SATURATION;
}

float readBatteryV() {
  return analogReadMilliVolts(PIN_BATT) * 2.0f / 1000.0f;       // 1:2 divider
}

void publishTelemetry() {
  float t = dht.readTemperature(), h = dht.readHumidity();
  if (isnan(t) || isnan(h)) return;                            // skip bad DHT reads
  StaticJsonDocument<256> doc;
  doc["node_id"] = NODE_ID;
  doc["zone"] = ZONE;
  doc["soil_moisture"] = round(readSoilVwc() * 10) / 10.0;
  doc["air_temp"] = round(t * 10) / 10.0;
  doc["humidity"] = round(h * 10) / 10.0;
  doc["battery"] = round(readBatteryV() * 100) / 100.0;
  char buf[256];
  size_t n = serializeJson(doc, buf);
  mqtt.publish(topicTelemetry().c_str(), (const uint8_t*)buf, n, false);
}

void setup() {
  pinMode(PIN_RELAY, OUTPUT);
  setValve(false);                       // fail-safe: valve closed at boot
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_SOIL, ADC_11db);
  dht.begin();
  Serial.begin(115200);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMessage);
  wifiConnect();
}

uint32_t lastSample = 0;

void loop() {
  if (WiFi.status() != WL_CONNECTED) wifiConnect();
  if (WiFi.status() == WL_CONNECTED) { mqttConnect(); mqtt.loop(); }

  // Local fail-safe: close the valve on timeout even if the network is down.
  if (valveOpen && (int32_t)(millis() - valveCloseAtMs) >= 0) setValve(false);

  if (millis() - lastSample >= SAMPLE_PERIOD_S * 1000UL || lastSample == 0) {
    lastSample = millis();
    if (mqtt.connected()) publishTelemetry();
  }
  delay(50);
}
