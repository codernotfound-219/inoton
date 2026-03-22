import asyncio
import uuid
import time
from typing import AsyncIterator
from threading import Lock

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


_cmd_lock = Lock()
_pending_cmd: dict[str, dict] = {}


def _new_command_id() -> str:
    return uuid.uuid4().hex


def _publish_json(topic: str, payload: dict) -> None:
    if _mqtt_client is None:
        raise RuntimeError("MQTT client not initialized")
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    # QoS 1 for control messages (at-least-once delivery)
    _mqtt_client.publish(topic, data, qos=1, retain=False)


def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT connected. Subscribing...")
        client.subscribe(settings.TOPIC_TELEMETRY)
        client.subscribe(settings.TOPIC_HIGH_FREQ)
        client.subscribe("microgrid/control/ack")
    else:
        print(f"❌ MQTT connect failed. rc={rc}")


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic

        if topic == settings.TOPIC_TELEMETRY:
            state.solar_watts = payload.get("solar_w", state.solar_watts)
            # SOC is authoritative from the battery controller ESP only
            if payload.get("device_id") == "battery" and "soc" in payload:
                state.battery_soc = payload.get("soc", state.battery_soc)
            state.total_load = payload.get("load_w", state.total_load)
            state.bus_v = payload.get("bus_v", state.bus_v)
        elif topic == settings.TOPIC_HIGH_FREQ:
            state.current_a = payload.get("current", state.current_a)
        elif topic == "microgrid/control/ack":
            cmd_id = payload.get("command_id")
            status = payload.get("status")
            applied = payload.get("applied") or {}
            if cmd_id:
                with _cmd_lock:
                    _pending_cmd[cmd_id] = {
                        "status": status,
                        "device_id": payload.get("device_id"),
                        "applied": applied,
                        "ts": time.time(),
                    }

            # Update relay states if present
            if "relay1" in applied:
                state.relay_load1 = bool(applied["relay1"])
                state.relay_status = state.relay_load1
            if "relay2" in applied:
                state.relay_load2 = bool(applied["relay2"])

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


@app.post("/api/control/relays")
def set_relays(body: dict) -> dict:
    """Set relay states via MQTT.

    Body example:
      {"relay1": true, "relay2": false, "target": "all"}
    """
    cmd_id = _new_command_id()
    target = body.get("target") or "all"
    data: dict = {}
    if "relay1" in body:
        data["relay1"] = bool(body["relay1"])
    if "relay2" in body:
        data["relay2"] = bool(body["relay2"])

    msg = {
        "v": 1,
        "command_id": cmd_id,
        "ts": int(time.time() * 1000),
        "source": "digital-twin",
        "target": target,
        "type": "set_relays",
        "data": data,
        "ttl_ms": 3000,
    }
    _publish_json(settings.TOPIC_CONTROL, msg)
    return {"ok": True, "command_id": cmd_id}


@app.post("/api/control/shed")
def shed_load(body: dict) -> dict:
    """Shed one load based on smallest load value.

    Body example:
      {"bus_v": 7.9}
    """
    cmd_id = _new_command_id()

    # Decide which load is smaller based on current state split (until per-load telemetry arrives).
    # Frontend and state currently derive load split; backend keeps it simple.
    load1_est = state.total_load * 0.55
    load2_est = state.total_load * 0.45
    which = "load1" if load1_est <= load2_est else "load2"

    msg = {
        "v": 1,
        "command_id": cmd_id,
        "ts": int(time.time() * 1000),
        "source": "digital-twin",
        "target": "all",
        "type": "shed_load",
        "data": {"which": which},
        "ttl_ms": 3000,
    }
    _publish_json(settings.TOPIC_CONTROL, msg)
    return {"ok": True, "command_id": cmd_id, "which": which}


@app.post("/api/control/battery_mode")
def set_battery_mode(body: dict) -> dict:
    """Set battery controller mode.

    Body example:
      {"mode": "CHARGE"}  # CHARGE | DISCHARGE | IDLE | AUTO
    """
    cmd_id = _new_command_id()
    mode = (body.get("mode") or "").upper()
    if mode not in {"CHARGE", "DISCHARGE", "IDLE", "AUTO"}:
        return {"ok": False, "error": "invalid mode", "allowed": ["CHARGE", "DISCHARGE", "IDLE", "AUTO"]}

    msg = {
        "v": 1,
        "command_id": cmd_id,
        "ts": int(time.time() * 1000),
        "source": "digital-twin",
        "target": "battery",
        "type": "battery_mode",
        "data": {"mode": mode},
        "ttl_ms": 5000,
    }
    _publish_json(settings.TOPIC_CONTROL, msg)
    return {"ok": True, "command_id": cmd_id, "mode": mode}


@app.post("/api/control/fault/short_circuit")
def simulate_short_circuit_fault(body: dict | None = None) -> dict:
    """Simulate a short-circuit fault.

    Behavior:
    - Latches a fault flag in the in-memory twin state
    - Opens (disconnects) all load relays via MQTT
    - Forces the battery controller to IDLE via MQTT
    """
    cmd_id_relays = _new_command_id()
    cmd_id_batt = _new_command_id()

    state.fault_active = True
    state.fault_code = "SHORT_CIRCUIT"
    state.fault_reason = (body or {}).get("reason") or "Simulated short circuit fault"
    state.last_updated = time.time()

    relays_msg = {
        "v": 1,
        "command_id": cmd_id_relays,
        "ts": int(time.time() * 1000),
        "source": "digital-twin",
        "target": "all",
        "type": "set_relays",
        "data": {"relay1": False, "relay2": False},
        "ttl_ms": 5000,
    }
    _publish_json(settings.TOPIC_CONTROL, relays_msg)

    batt_msg = {
        "v": 1,
        "command_id": cmd_id_batt,
        "ts": int(time.time() * 1000),
        "source": "digital-twin",
        "target": "battery",
        "type": "battery_mode",
        "data": {"mode": "IDLE"},
        "ttl_ms": 5000,
    }
    _publish_json(settings.TOPIC_CONTROL, batt_msg)

    return {
        "ok": True,
        "fault_active": True,
        "fault_code": state.fault_code,
        "command_id_relays": cmd_id_relays,
        "command_id_battery": cmd_id_batt,
    }


@app.post("/api/control/fault/clear")
def clear_fault() -> dict:
    """Clear latched fault flags in the twin.

    Note: this does not automatically re-close relays; it only unlatches the fault.
    """
    state.fault_active = False
    state.fault_code = None
    state.fault_reason = None
    state.last_updated = time.time()
    return {"ok": True, "fault_active": False}


@app.get("/api/control/commands/{command_id}")
def get_command(command_id: str) -> dict:
    with _cmd_lock:
        return _pending_cmd.get(command_id, {"status": "unknown"})


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
