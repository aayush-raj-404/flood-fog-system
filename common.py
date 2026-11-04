"""common.py - small helpers shared by every component."""

import json
import time

import paho.mqtt.client as mqtt

import config


def log(tag, message):
    """Print a timestamped, tagged log line (plain ASCII so Windows consoles are happy)."""
    print(f"{time.strftime('%H:%M:%S')} [{tag}] {message}", flush=True)


def make_client(client_id):
    """Create a paho-mqtt (v2 API) client."""
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=True)


def connect(client, tag, retries=30):
    """Connect to the local MQTT broker, retrying while it starts up."""
    for attempt in range(retries):
        try:
            client.connect(config.MQTT_HOST, config.MQTT_PORT, keepalive=30)
            return
        except OSError:
            if attempt == 0:
                log(tag, f"waiting for MQTT broker at {config.MQTT_HOST}:{config.MQTT_PORT} ...")
            time.sleep(1)
    raise SystemExit(f"[{tag}] Could not reach the MQTT broker. Is Mosquitto running?")


def to_json(obj):
    return json.dumps(obj, separators=(",", ":"))


def from_json(payload):
    return json.loads(payload.decode("utf-8") if isinstance(payload, bytes) else payload)


def level_rank(level):
    return config.ALERT_LEVELS.index(level)
