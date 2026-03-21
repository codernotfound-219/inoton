import matplotlib.pyplot as plt

def plot_microgrid_performance(df, hours_to_show=48):
    """Visualizes the supply/demand balance for the first N hours."""
    df_sample = df.iloc[:288 * (hours_to_show // 24)]
    plt.figure(figsize=(12, 6))
    plt.plot(df_sample.index, df_sample['solar_irradiance_w'], label='Solar Supply', color='orange')
    plt.plot(df_sample.index, df_sample['total_load_w'], label='Total Load', color='black', linestyle='--')
    plt.fill_between(df_sample.index, df_sample['solar_irradiance_w'], df_sample['total_load_w'], 
                     where=(df_sample['total_load_w'] > df_sample['solar_irradiance_w']),
                     color='red', alpha=0.2, label='Energy Deficit')
    plt.title("Supply vs Demand Balance")
    plt.legend()
    plt.show()

def plot_hf_transition(df_hf, transition_point):
    """Visualizes the transition from normal to fault states."""
    plt.figure(figsize=(15, 5))
    plt.plot(df_hf.index[:transition_point], df_hf['current_a'][:transition_point], color='green')
    plt.plot(df_hf.index[transition_point:], df_hf['current_a'][transition_point:], color='red')
    plt.axvline(x=transition_point, color='black', linestyle='--')
    plt.title("HF Current Transition (Normal vs Fault)")
    plt.show()
