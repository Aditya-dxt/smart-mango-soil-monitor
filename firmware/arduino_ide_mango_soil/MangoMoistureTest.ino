#include <Arduino.h>
#include <DHT.h>
#include <math.h>

// ESP32 Dev Module pins:
// Capacitive soil sensor AO -> GPIO34
// DHT11 DATA -> GPIO4
// PH-4502C PO -> 10k/10k divider -> GPIO35
// All grounds must be connected together.
#define SOIL_PIN 34
#define DHT_PIN 4
#define DHT_TYPE DHT11
#define PH_PIN 35

// Soil ADC endpoints previously measured for this sensor.
static const int SOIL_DRY_ADC = 2037;
static const int SOIL_WET_ADC = 1316;

// Entered pH calibration values, in estimated PO volts BEFORE the divider.
// Verify with pH 4.00 and 7.00 buffer solutions before trusting pH.
static const float PH4_VOLTAGE = 0.517f;
static const float PH7_VOLTAGE = 0.340f;

static const uint32_t SAMPLE_INTERVAL_MS = 2500;
static uint32_t lastSampleMs = 0;
DHT dht(DHT_PIN, DHT_TYPE);

int readAverageAdc(uint8_t pin) {
  uint32_t sum = 0;
  constexpr uint8_t samples = 32;
  for (uint8_t i = 0; i < samples; ++i) {
    sum += analogRead(pin);
    delay(4);
  }
  return static_cast<int>(sum / samples);
}

float readAveragePhOutputVoltage() {
  uint32_t sumMilliVoltsAtPin = 0;
  constexpr uint8_t samples = 32;
  for (uint8_t i = 0; i < samples; ++i) {
    sumMilliVoltsAtPin += analogReadMilliVolts(PH_PIN);
    delay(4);
  }
  // A 10k/10k divider halves voltage; multiply by two to estimate module PO.
  return (sumMilliVoltsAtPin / static_cast<float>(samples)) / 500.0f;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(SOIL_PIN, ADC_11db);
  analogSetPinAttenuation(PH_PIN, ADC_11db);
  dht.begin();
  delay(1500);
  Serial.println();
  Serial.println("Mango Soil - LOCAL SERIAL MODE (no Wi-Fi or Firebase)");
  Serial.println("Serial Monitor speed: 115200 baud; updates every 2.5 seconds.");
  Serial.println("Unconnected sensors may show invalid or unstable readings.");
  Serial.println("pH is an estimate until PH4/PH7 values are verified with buffers.");
}

void loop() {
  const uint32_t now = millis();
  if (now - lastSampleMs < SAMPLE_INTERVAL_MS) return;
  lastSampleMs = now;

  const int soilAdc = readAverageAdc(SOIL_PIN);
  const int phAdc = readAverageAdc(PH_PIN);
  const float temperatureC = dht.readTemperature();
  const float humidity = dht.readHumidity();
  const float phVoltage = readAveragePhOutputVoltage();

  Serial.print("soil_moisture_adc="); Serial.print(soilAdc);
  Serial.print(" | soil_moisture_percent=");
  if (SOIL_DRY_ADC != SOIL_WET_ADC) {
    const float percent = 100.0f * (SOIL_DRY_ADC - soilAdc) /
                          (SOIL_DRY_ADC - SOIL_WET_ADC);
    Serial.print(constrain(percent, 0.0f, 100.0f), 1);
  } else Serial.print("uncalibrated");

  Serial.print(" | temperature_C=");
  if (isfinite(temperatureC)) Serial.print(temperatureC, 1);
  else Serial.print("invalid");
  Serial.print(" | humidity_RH_percent=");
  if (isfinite(humidity)) Serial.print(humidity, 1);
  else Serial.print("invalid");

  Serial.print(" | soil_pH_estimate=");
  if (PH4_VOLTAGE > 0.0f && PH7_VOLTAGE > 0.0f &&
      fabsf(PH7_VOLTAGE - PH4_VOLTAGE) > 0.001f) {
    const float pH = 4.0f + (phVoltage - PH4_VOLTAGE) * 3.0f /
                     (PH7_VOLTAGE - PH4_VOLTAGE);
    if (pH >= 0.0f && pH <= 14.0f) Serial.print(pH, 2);
    else Serial.print("out_of_range");
  } else Serial.print("uncalibrated");

  Serial.print(" | PH4502C_PO_voltage_before_divider_V=");
  Serial.print(phVoltage, 3);
  Serial.print(" | ph_adc_GPIO35="); Serial.println(phAdc);
}