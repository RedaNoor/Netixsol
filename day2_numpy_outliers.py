import numpy as np

# 1. Generate Synthetic Sensor Data (30 timesteps of 3 sensors)
np.random.seed(42)  # For reproducible results
time_steps = 30
num_sensors = 3

# Baseline trend + noise + some injected extreme outliers
base_data = np.random.normal(loc=25.0, scale=2.0, size=(time_steps, num_sensors))
# Inject artificial anomalies (outliers)
base_data[5, 0] = 40.0
base_data[15, 1] = 5.0
base_data[25, 2] = 42.0

sensor_data = base_data
print("--- Raw Sensor Data Shape ---")
print(sensor_data.shape)  # Should be (30, 3)

print("\nFirst 3 rows of raw data:\n", sensor_data[:3])


# 2. Compute Rolling Statistics (Window size = 5)
window_size = 5
windows = np.lib.stride_tricks.sliding_window_view(sensor_data, window_shape=window_size, axis=0)

rolling_mean = np.mean(windows, axis=-1)
rolling_std = np.std(windows, axis=-1)

print(f"\n--- Rolling Statistics (Window Size = {window_size}) ---")
print(f"Rolling Mean Shape: {rolling_mean.shape}")  # (26, 3)
print("First 3 rows of Rolling Mean:\n", rolling_mean[:3])


# 3. Normalize Data (Z-score normalization over the entire dataset per sensor)
global_mean = np.mean(sensor_data, axis=0)
global_std = np.std(sensor_data, axis=0)

normalized_data = (sensor_data - global_mean) / global_std

print("\n--- Global Stats per Sensor ---")
print("Global Means:", global_mean)
print("Global Std Devs:", global_std)
print("\nFirst 3 rows of Normalized Data (Z-Scores):\n", normalized_data[:3])


# 4. Flag Outliers (Z-score threshold > 2 or < -2 standard deviations)
outlier_mask = np.abs(normalized_data) > 2.0
outlier_indices = np.argwhere(outlier_mask)

print("\n--- Detected Outliers (> 2 standard deviations) ---")
print(f"Total outliers found: {np.sum(outlier_mask)}")
print("\nIndex [Row, Sensor] and corresponding Raw Value:")
for idx in outlier_indices:
    row, col = idx[0], idx[1]
    val = sensor_data[row, col]
    z_score = normalized_data[row, col]
    print(f"Row {row:2d}, Sensor {col}: Raw Value = {val:5.2f} (Z-score = {z_score:+5.2f})")
