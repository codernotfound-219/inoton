from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MQTT Configuration
    MQTT_BROKER: str = "172.20.10.8" 
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
