import asyncio
import time
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import json
from paho.mqtt import client as mqtt_client

from config import settings

from state import MicrogridState


app = FastAPI(title="Digital Twin API", version="0.1.0")

# Dev-friendly CORS (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory singleton state. Updated by MQTT ingestion in main.py
state = MicrogridState()


def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT connected. Subscribing...")
        client.subscribe(settings.TOPIC_TELEMETRY)
        client.subscribe(settings.TOPIC_HIGH_FREQ)
    else:
        print(f"❌ MQTT connect failed. rc={rc}")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic

        if topic == settings.TOPIC_TELEMETRY:
            state.solar_watts = payload.get("solar_w", state.solar_watts)
            state.battery_soc = payload.get("soc", state.battery_soc)
            state.total_load = payload.get("load_w", state.total_load)
        elif topic == settings.TOPIC_HIGH_FREQ:
            state.current_a = payload.get("current", state.current_a)

        state.last_updated = time.time()
    except Exception as e:
        print(f"⚠️ Telemetry Parse Error: {e}")


_mqtt_client: mqtt_client.Client | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _mqtt_client
    # Connect MQTT in a non-blocking way.
    client = mqtt_client.Client()
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.connect(settings.MQTT_BROKER, settings.MQTT_PORT)
    client.loop_start()
    _mqtt_client = client


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _mqtt_client
    if _mqtt_client is not None:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
        _mqtt_client = None


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/state", response_model=MicrogridState)
def get_state() -> MicrogridState:
    return state


async def _state_stream(interval_s: float = 0.5) -> AsyncIterator[dict]:
    while True:
        payload = state.model_dump()
        payload["last_updated"] = time.time()
        yield payload
        await asyncio.sleep(interval_s)


@app.websocket("/ws")
async def ws_state(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        async for payload in _state_stream():
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        return


# Future: commands to ESP32.
# Keep for later to avoid locking in a control schema prematurely.
# @app.post("/api/control")
# def control(...):
#     ...
