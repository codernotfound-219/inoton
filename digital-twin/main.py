import asyncio
import json
import uvicorn
from paho.mqtt import client as mqtt_client
from config import settings
from state import MicrogridState
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# 1. Initialization
state = MicrogridState()
app = FastAPI(title="Microgrid Digital Twin")
active_connections = set()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2.1 INIT
@app.get("/")
async def root():
    """Health check endpoint to verify server status."""
    return {"status": "online", "system": "Microgrid Digital Twin"}

# 2.2 HTTP Endpoints
@app.get("/state")
async def get_state():
    return state.dict()

# 3. WebSocket Endpoint (The Live Pipe)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            # Keep the connection open
            await websocket.receive_text() 
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# 4. Background Orchestration
@app.on_event("startup")
async def startup_event():
    # Start MQTT and WebSocket broadcast loops
    asyncio.create_task(run_mqtt())
    asyncio.create_task(broadcast_state())

async def broadcast_state():
    while True:
        if active_connections:
            data = state.json()
            for connection in list(active_connections):
                try:
                    await connection.send_text(data)
                except:
                    active_connections.remove(connection)
        await asyncio.sleep(0.5)

# 5. MQTT Logic (Ingestion)
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Connected.")
        client.subscribe(settings.TOPIC_TELEMETRY)
        client.subscribe(settings.TOPIC_HIGH_FREQ)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if msg.topic == settings.TOPIC_TELEMETRY:
            state.solar_watts = payload.get("solar_w", state.solar_watts)
            state.battery_soc = payload.get("soc", state.battery_soc)
            state.total_load = payload.get("load_w", state.total_load)
        elif msg.topic == settings.TOPIC_HIGH_FREQ:
            state.current_a = payload.get("current", state.current_a)
    except Exception as e:
        print(f"⚠️ Error: {e}")

async def run_mqtt():
    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.MQTT_BROKER, settings.MQTT_PORT)
    client.loop_start()
    while True:
        await asyncio.sleep(1)

# 6. FIXED ENTRY POINT
if __name__ == "__main__":
    print(f"🚀 Digital Twin starting on http://{settings.MQTT_BROKER}:{settings.WS_PORT}")
    uvicorn.run(app, host=settings.MQTT_BROKER, port=settings.WS_PORT)
