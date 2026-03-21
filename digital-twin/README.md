# Digital Twin — DC Microgrid Dashboard

A lightweight digital twin dashboard for a DC microgrid (Solar PV, Battery, regulated DC supply, and 2 loads).

- **Backend**: FastAPI + WebSocket stream; ingests MQTT telemetry and exposes state via HTTP/WS.
- **Frontend**: Vite + React + TypeScript dashboard (multi-page UI).

## Project Structure

- `api.py` — FastAPI app (`/api/state`, `/api/health`, `/ws`) + MQTT ingestion on startup
- `config.py` — settings (MQTT broker/port/topics) loaded from `.env` if present
- `state.py` — `MicrogridState` model
- `dashboard/` — Vite React UI

## Prerequisites

- Python 3.10+ (recommended)
- Node.js 18+ (recommended)
- MQTT broker (Mosquitto)

## Quick Start

### 1) Start Mosquitto

If you use Homebrew:

```bash
brew services start mosquitto
```

Or run it in the foreground:

```bash
mosquitto -p 1883
```

### 2) Start the backend (FastAPI)

From the repo root:

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

- `http://localhost:8000/api/health`

### 3) Start the frontend (Vite)

From `dashboard/`:

```bash
npm install
npm run dev
```

Then open the Vite URL (typically `http://localhost:5173`).

## Sending Sample Data (MQTT)

The backend subscribes to these topics (see `config.py`):

- `microgrid/telemetry` (JSON keys: `solar_w`, `soc`, `load_w`)
- `microgrid/sensors/current` (JSON key: `current`)

Example publishes:

```bash
mosquitto_pub -h MQTT_BROKER_IP -p 1883 -t microgrid/telemetry -m '{"solar_w":120,"soc":67.5,"load_w":180}'
mosquitto_pub -h MQTT_BROKER_IP -p 1883 -t microgrid/sensors/current -m '{"current":1.23}'
```

## Configuration

Settings are defined in `config.py` and can be overridden via environment variables.

If you want to use a `.env` file (recommended for local config), create one in the repo root:

```env
MQTT_BROKER=MQTT_BROKER_IP
MQTT_PORT=1883
TOPIC_TELEMETRY=microgrid/telemetry
TOPIC_HIGH_FREQ=microgrid/sensors/current
TOPIC_CONTROL=microgrid/control/relays
```

### Frontend backend host (optional)

By default, the frontend connects to `http://localhost:8000` and `ws://localhost:8000`.

To override (useful when accessing the UI from another device), create `dashboard/.env`:

```env
VITE_BACKEND_HOST=localhost
VITE_BACKEND_PORT=8000
VITE_BACKEND_HTTP_PROTO=http
VITE_BACKEND_WS_PROTO=ws
```

## Notes

- The UI “Connected/Offline” indicator reflects whether the frontend can receive state from the backend (`/ws` or `/api/state`). If the backend isn’t running, the UI will show Offline and MQTT publishes won’t appear.
- Future control channel is reserved at `microgrid/control/relays` but the UI is currently read-only.
