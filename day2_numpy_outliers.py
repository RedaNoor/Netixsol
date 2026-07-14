import numpy as np

sensor = np.array([
    18, 19, 20, 21, 22,
    23, 24, 60, 25, 26,
    27, 2, 28, 29, 30, 31
])
print("--- Raw Sensor Data ---")
print(sensor)

window = 4

# 2. Rolling statistics
rolling_mean = np.convolve(sensor, np.ones(window) / window, mode='valid')

rolling_std = np.array([
    np.std(sensor[i:i + window]) for i in range(len(sensor) - window + 1)
])

print(f"\n--- Rolling Statistics (Window Size = {window}) ---")
print("Rolling Mean:", rolling_mean)
print("Rolling Std :", rolling_std)

# 3. Z-score normalization
mean = np.mean(sensor)
std = np.std(sensor)
zscores = (sensor - mean) / std

print("\n--- Z-Score Normalization ---")
print("Mean:", mean, "| Std:", std)
print("Z-Scores:", zscores)

outlier_mask = np.abs(zscores) > 2
outlier_indices = np.where(outlier_mask)[0]

print("\n--- Outliers Detected (> 2 Std Dev) ---")
if len(outlier_indices) > 0:
    for idx in outlier_indices:
        print(f"Index {idx:2d}: Value = {sensor[idx]:5.2f}  Z-Score = {zscores[idx]:+5.2f}")
else:
    print("No outliers detected.")
