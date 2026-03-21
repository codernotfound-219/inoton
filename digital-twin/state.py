from pydantic import BaseModel
from typing import Optional

class MicrogridState(BaseModel):
    # Hardware Inputs (Received via MQTT)
    solar_watts: float = 0.0
    battery_soc: float = 100.0
    battery_temp: float = 25.0
    total_load: float = 0.0
    current_a: float = 0.0
    
    # Model Outputs (Inputs from your teammate's AI)
    predicted_load: float = 0.0
    predicted_solar: float = 0.0
    anomaly_score: float = 0.0
    
    # Control & Logic States (Derived by your Twin)
    relay_status: bool = True       # True = Closed (On)
    active_source: str = "Solar"    # "Solar", "Battery", or "Grid"
    
    # Meta Info
    last_updated: float = 0.0
