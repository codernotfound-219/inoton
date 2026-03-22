from pydantic import BaseModel
from typing import Optional

class MicrogridState(BaseModel):
    # Hardware Inputs (Received via MQTT)
    solar_watts: float = 0.0
    battery_soc: float = 100.0
    battery_temp: float = 25.0
    total_load: float = 0.0
    current_a: float = 0.0
    bus_v: float = 0.0
    
    # Model Outputs (Inputs from your teammate's AI)
    predicted_load: float = 0.0
    predicted_solar: float = 0.0
    anomaly_score: float = 0.0
    
    # Control & Logic States (Derived by your Twin)
    # Relay states (True = Closed/On). relay_status kept for backward compatibility (mirrors load1).
    relay_status: bool = True
    relay_load1: bool = True
    relay_load2: bool = True
    active_source: str = "Solar"    # "Solar", "Battery", or "Grid"
    
    # Meta Info
    last_updated: float = 0.0

    # Fault Simulation (latched)
    fault_active: bool = False
    fault_code: Optional[str] = None
    fault_reason: Optional[str] = None
