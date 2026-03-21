# Synthetic Data Generation Engine for Microgrid Simulation

## 1. Overview
This repository contains a modular Python-based engine designed to generate physically-plausible synthetic datasets for microgrid simulation:

1. **Low-Frequency Telemetry:** 30 days of 5-minute interval data for load forecasting and energy management.
2. **High-Frequency Current Waveforms:** 20Hz sampling for anomaly detection and fault modeling.

## 2. Directory Architecture

```text
project_root/
|
|-- data_gen/
|   |-- __init__.py
|   |-- config.py        # Static physical constants and simulation parameters
|   |-- models.py        # Vectorized mathematical generation logic
|   |-- visualizer.py    # Diagnostic plotting and verification utilities
|
|-- main.py              # Orchestration script for data export and visualization
|-- README.md            # Technical documentation and mathematical framework
```

## 3. Mathematical Framework

### 3.1 Environmental Variables
To ensure the datasets exhibit temporal persistence and physical coupling, the environment is modeled with the following logic:

**Cloud Cover ($C$):**
Generated via a smoothed random walk to simulate slow-moving weather fronts:

$$
C_t = \frac{1}{k} \sum_{i=t-k/2}^{t+k/2} \mathrm{Uniform}(0, 1)_i
$$

Where $k = 24$ (representing a 2-hour rolling average).

**Diurnal Temperature ($T$):**
A sinusoidal function of the hour ($H$) adjusted by cloud-induced thermal attenuation:

$$
T(H, C) = T_{\mathrm{mean}} + T_{\mathrm{amp}} \cdot \sin\left(\frac{2\pi(H - 9)}{24}\right) - (5.0 \cdot C) + \epsilon
$$

Where $\epsilon \sim \mathcal{N}(0, 0.5)$ provides localized Gaussian noise.

### 3.2 Power Supply and Demand
The microgrid’s electrical state is derived directly from environmental inputs to ensure consistency.

**Solar Irradiance ($W_{\mathrm{solar}}$):**
Modeled as a cosine distribution centered at solar noon ($H = 12$):

$$
W_{\mathrm{solar}} = P_{\max} \cdot \max\left(0, \cos\left(\frac{\pi(H - 12)}{12}\right)\right) \cdot (1 - 0.75 \cdot C)
$$

**Departmental Load ($L_{\mathrm{dept}}$):**
Simulates academic usage with non-linear thermal coupling for HVAC systems:

$$
L_{\mathrm{dept}} = L_{\mathrm{base}} + \mathrm{Activity}(H) + \alpha \cdot \max(0, T - 30)
$$

Where $\alpha = 20\,\mathrm{W}/^\circ\mathrm{C}$ represents the air conditioning power coefficient.

**Hostel Load ($L_{\mathrm{hostel}}$):**
Simulates residential usage peaking between 18:00 and 02:00:

$$
L_{\mathrm{hostel}} = L_{\mathrm{base}} + \mathrm{ResidentialActivity}(H)
$$

### 3.3 High-Frequency Anomaly Modeling
Current waveforms are generated at 20Hz ($f_s$) to simulate high-resolution sensor streams.

**Normal State ($I_{\mathrm{normal}}$):**
A stable DC signal with a periodic ripple and sensor jitter:

$$
I_{\mathrm{normal}}(t) = I_{\mathrm{dc}} + 0.2 \cdot \sin(2\pi \cdot 0.5 \cdot t) + \mathcal{N}(0, 0.1)
$$

**Anomaly State ($I_{\mathrm{fault}}$):**
A high-entropy signal simulating a short circuit:

$$
I_{\mathrm{fault}}(t) = I_{\mathrm{dc}} + \mathcal{N}(0, 5.0) + \mathrm{Spikes}(20\mathrm{A})
$$

## 4. Execution
To generate the datasets and verify the physical curves:

1. Verify Python 3.11 environment.
2. Install dependencies: `pip install pandas numpy matplotlib`.
3. Execute `python main.py`.

**Outputs:**

- `synthetic_energy_data.csv`: Main telemetry for LSTM/RL training.
- `high_frequency_current.csv`: Raw current data for Autoencoder training.

---