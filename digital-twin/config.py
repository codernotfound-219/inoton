from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MQTT Configuration
    # Provide via environment/.env (see .env.example). Defaults to localhost.
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    
    # Topic Definitions (Standardize these now to avoid mismatches)
    TOPIC_TELEMETRY: str = "microgrid/telemetry"      # 5-min averages
    TOPIC_HIGH_FREQ: str = "microgrid/sensors/current" # 20Hz stream
    TOPIC_CONTROL: str = "microgrid/control/relays"   # Commands to ESP32
    
    # WebSocket Configuration
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
