import asyncio
import json
from paho.mqtt import client as mqtt_client
from config import settings
from state import MicrogridState

state = MicrogridState()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connection Successful. Subscribing to telemetry streams...")
        # Subscribe to the topics we defined in config.py
        client.subscribe(settings.TOPIC_TELEMETRY)
        client.subscribe(settings.TOPIC_HIGH_FREQ)
    else:
        print(f"❌ Connection Failed. Return Code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic

        if topic == settings.TOPIC_TELEMETRY:
            # Map json keys to the state object
            state.solar_watts = payload.get("solar_w", state.solar_watts)
            state.battery_soc = payload.get("soc", state.battery_soc)
            state.total_load = payload.get("load_w", state.total_load)
            print(f"📊 State Updated: Solar={state.solar_watts}W | SOC={state.battery_soc}%")
        elif topic == settings.TOPIC_HIGH_FREQ:
            state.current_a = payload.get("current", state.current_a)
            # INFO: add the anamoly detection trigger here

    except Exception as e:
        # Crucial for a hackathon: Don't let a single bad packet crash the Twin.
        print(f"⚠️ Telemetry Parse Error: {e}")
