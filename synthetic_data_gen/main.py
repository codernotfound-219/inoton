from data_gen import models, visualizer, config
import pandas as pd
import numpy as np

def run_pipeline():
    print("--- Starting Synthetic Data Generation ---")
    
    # 1. 5-Minute Telemetry Generation
    df = models.generate_base_df()
    df = models.apply_environmental_models(df)
    df = models.apply_power_metrics(df)
    df.to_csv("synthetic_energy_data.csv", index=False)
    print("Main Telemetry Exported.")
    
    # 2. High-Frequency Generation
    norm = models.generate_hf_waveform(config.DURATION_NORMAL, is_anomaly=False)
    fault = models.generate_hf_waveform(config.DURATION_FAULT, is_anomaly=True)
    
    df_hf = pd.DataFrame({
        'current_a': np.concatenate([norm, fault]),
        'label': np.concatenate([np.zeros(len(norm)), np.ones(len(fault))])
    })
    df_hf.to_csv("high_frequency_current.csv", index=False)
    print("HF Data Exported.")
    
    # 3. Visualization
    visualizer.plot_microgrid_performance(df)
    visualizer.plot_hf_transition(df_hf, len(norm))

if __name__ == "__main__":
    run_pipeline()
