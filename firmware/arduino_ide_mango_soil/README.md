# Arduino IDE sensor test firmware

This folder contains the serial-only ESP32 sketch used to check the current sensor set before reconnecting any cloud service.

## Current sensors

- Capacitive soil-moisture sensor (raw ADC and estimated percentage)
- DHT11 air temperature and relative humidity
- PH-4502C analog pH interface (raw ADC, estimated module output voltage, and a pH estimate when calibration values are enabled)

The sketch prints one line every 2.5 seconds at **115200 baud**. It does not connect to Wi-Fi, Firebase, or MQTT.

## Board and wiring

Select **ESP32 Dev Module** in Arduino IDE. Current pin mapping:

| Part | Connection |
|---|---|
| Capacitive moisture sensor AO | ESP32 GPIO34 |
| DHT11 DATA | ESP32 GPIO4 |
| DHT11 VCC/GND | Appropriate supply/GND; use a pull-up from DATA to VCC if the module does not include one |
| PH-4502C PO | Voltage divider midpoint to ESP32 GPIO35 |
| PH-4502C VCC/GND | Module supply and common ground with ESP32 |

The sketch assumes a **10 kΩ / 10 kΩ divider** between PH-4502C PO and ground, with GPIO35 at the midpoint. This halves PO voltage; code estimates the voltage before the divider by doubling the measured pin voltage. Confirm the module output and divider with a multimeter before connecting to the ESP32. Never let an ESP32 ADC pin exceed its permitted input voltage. Grounds must be common.

## Arduino IDE setup

1. Install Arduino IDE 2.x and the Espressif **esp32** board package.
2. In **Tools → Board**, select **ESP32 Dev Module**; select the correct serial port when the board is connected.
3. Install these libraries using **Sketch → Include Library → Manage Libraries**:
   - **DHT sensor library** by Adafruit
   - **Adafruit Unified Sensor** (dependency of the DHT library)
4. Open `MangoMoistureTest.ino`, choose **115200 baud** in Serial Monitor, then verify and upload.

The sketch uses the ESP32 Arduino core's built-in `Arduino.h`, ADC functions, and math library. No Firebase library or cloud configuration is needed for this serial-only test.

## Calibration and interpretation

- Moisture percentage maps `SOIL_DRY_ADC=2037` to 0% and `SOIL_WET_ADC=1316` to 100%. These are setup-specific reference readings, not a universal physical moisture scale. Re-measure with the probe in the same soil and installation for reproducible results.
- `PH4_VOLTAGE=0.517` and `PH7_VOLTAGE=0.340` are the entered calibration values in estimated PH-4502C **PO volts before the divider**. The sketch calculates a pH estimate from them, but values are not verified unless measured using proper pH 4.00 and pH 7.00 buffer solutions with the probe and module adjusted and settled. pH values outside 0–14 are rejected. Do not treat estimates as laboratory measurements.
- The PH-4502C voltage output and ESP32 ADC reading can vary with board, ADC characteristics, supply, wiring, and probe conditioning. Use raw readings for diagnosis.
- DHT11 updates slowly and has limited accuracy. Invalid readings generally indicate wiring, power, signal pull-up, or sampling issues.

## Serial fields

`soil_moisture_adc`, `soil_moisture_percent`, `temperature_C`, `humidity_RH_percent`, `soil_pH_estimate`, `PH4502C_PO_voltage_before_divider_V`, and `ph_adc_GPIO35`.

The percentage and pH are calculated estimates. Raw ADC values and sensor outputs are the direct measurements.

## Local secrets and data

Do not add Wi-Fi passwords, Firebase API keys/configuration, service credentials, authentication tokens, or private serial captures to Git. Keep such values in an untracked local header (for example `cloud_config.h`). This sketch does not need that file. The local `.gitignore` in this folder excludes common secret headers and serial logs.
