"""MQTT <-> backend bridge. Topics: orchard/<zone>/telemetry (in), orchard/<zone>/cmd (out)."""
import json, logging, os

log = logging.getLogger("mqtt")


class MqttBridge:
    def __init__(self, on_telemetry):
        self.on_telemetry, self.client = on_telemetry, None

    def start(self):
        host = os.getenv("MQTT_HOST")
        if not host:
            log.info("MQTT_HOST not set; MQTT bridge disabled (HTTP ingest still works).")
            return
        try:
            import paho.mqtt.client as mqtt
            try:
                c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            except AttributeError:
                c = mqtt.Client()
            if os.getenv("MQTT_USER"):
                c.username_pw_set(os.getenv("MQTT_USER"), os.getenv("MQTT_PASS", ""))
            c.on_connect = lambda cl, *a, **k: cl.subscribe("orchard/+/telemetry")
            c.on_message = self._msg
            c.connect(host, int(os.getenv("MQTT_PORT", "1883")), 60)
            c.loop_start()
            self.client = c
        except Exception as e:  # broker down must not stop the API
            log.warning("MQTT bridge failed to start: %s", e)

    def _msg(self, client, userdata, m):
        try:
            self.on_telemetry(json.loads(m.payload.decode()))
        except Exception as e:
            log.warning("bad telemetry payload: %s", e)

    def send_command(self, zone: str, minutes: int):
        if self.client:
            self.client.publish(f"orchard/{zone}/cmd", json.dumps({"minutes": minutes}), qos=1)
