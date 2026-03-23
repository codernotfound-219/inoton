# Innothon — Campus Grid Digital Twin

This repo contains a lightweight **digital twin for a campus DC microgrid / campus grid**.

At a high level:
- **ESP32 devices** publish telemetry to an **MQTT broker** (and can receive control commands).
- A **Python FastAPI backend** subscribes to MQTT, maintains an in-memory twin state, and exposes it over **HTTP + WebSocket**.
- A **Vite + React dashboard** visualizes the state and can issue control actions (relays, load shedding, battery mode, fault simulation).
- A **synthetic data generator** produces physically plausible datasets for forecasting/anomaly modeling.

## Repo Layout

- [digital-twin/](digital-twin/)
  - Backend: [digital-twin/api.py](digital-twin/api.py) (FastAPI + MQTT ingestion)
  - State model: [digital-twin/state.py](digital-twin/state.py)
  - Settings: [digital-twin/config.py](digital-twin/config.py) (loads from environment / `.env`)
  - Frontend: [digital-twin/dashboard/](digital-twin/dashboard/)
  - Arduino sketches (ESP32): `*.ino`
- [esp_mqtt_client/](esp_mqtt_client/) — standalone ESP32 MQTT client sketch
- [synthetic_data_gen/](synthetic_data_gen/) — synthetic telemetry + high-frequency current generator

## Quick Start (Local)

### 1) Run an MQTT broker

Using Homebrew Mosquitto:

```bash
brew services start mosquitto
```

Or run in the foreground:

```bash
mosquitto -p 1883
```

### 2) Configure backend environment

Create a local env file:

```bash
cp digital-twin/.env.example digital-twin/.env
```

Edit `digital-twin/.env` if your broker is not `localhost`.

### 3) Start the backend (FastAPI)

From the repo root:

```bash
python -m uvicorn digital-twin.api:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints:
- `GET /api/health`
- `GET /api/state`
- `WS /ws`

### 4) Start the dashboard (Vite + React)

```bash
cd digital-twin/dashboard
npm install
npm run dev
```

The UI defaults to backend `http://localhost:8000` and `ws://localhost:8000`.

Optional override (useful if hosting backend elsewhere): create `digital-twin/dashboard/.env`:

```env
VITE_BACKEND_HOST=localhost
VITE_BACKEND_PORT=8000
VITE_BACKEND_HTTP_PROTO=http
VITE_BACKEND_WS_PROTO=ws
```

## Sending Sample Telemetry

Default topics (see [digital-twin/config.py](digital-twin/config.py)):
- `microgrid/telemetry` (JSON keys like `solar_w`, `soc`, `load_w`, optional `bus_v`, `device_id`)
- `microgrid/sensors/current` (JSON key `current`)

Example publishes:

```bash
mosquitto_pub -h <MQTT_BROKER> -p 1883 -t microgrid/telemetry -m '{"device_id":"battery","solar_w":120,"soc":67.5,"load_w":180,"bus_v":8.1}'
mosquitto_pub -h <MQTT_BROKER> -p 1883 -t microgrid/sensors/current -m '{"current":1.23}'
```

## Control Plane (from Dashboard / API)

The backend publishes control messages to `microgrid/control/relays` and listens for acknowledgements on `microgrid/control/ack`.

Implemented API actions (see [digital-twin/api.py](digital-twin/api.py)):
- `POST /api/control/relays` — set relay states (relay1/relay2)
- `POST /api/control/shed` — choose a load to shed (simple heuristic)
- `POST /api/control/battery_mode` — set `CHARGE | DISCHARGE | IDLE | AUTO`
- `POST /api/control/fault/short_circuit` — simulate fault: latch in twin + open relays + force battery idle
- `POST /api/control/fault/clear` — clear latched fault in the twin

## ESP32 / Arduino Setup (Secrets)

WiFi SSID/password and broker host are **not committed**.

For sketches under [digital-twin/](digital-twin/) and [esp_mqtt_client/](esp_mqtt_client/):

1) Copy the example secrets header:

```bash
cp digital-twin/wifi_secrets.h.example digital-twin/wifi_secrets.h
cp esp_mqtt_client/wifi_secrets.h.example esp_mqtt_client/wifi_secrets.h
```

2) Edit each `wifi_secrets.h` with your local values.

These are gitignored via [.gitignore](.gitignore).

## Synthetic Data Generation

The generator in [synthetic_data_gen/](synthetic_data_gen/) outputs:
- low-frequency telemetry (5-minute intervals)
- high-frequency current waveforms (20Hz)

See [synthetic_data_gen/README.md](synthetic_data_gen/README.md) for details and equations.