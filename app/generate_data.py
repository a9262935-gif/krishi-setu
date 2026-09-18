@'
import os
import pandas as pd
import numpy as np

os.makedirs("data", exist_ok=True)
np.random.seed(42)

n_samples = 1200
dates = pd.date_range(start="2023-01-01", periods=n_samples, freq="D")
commodities = ["Wheat", "Paddy", "Maize", "Mustard", "Apple"]
districts = ["Rajouri", "Poonch", "Jammu", "Kathua", "Udhampur"]

data = {
    "Date": np.random.choice(dates, n_samples),
    "Commodity": np.random.choice(commodities, n_samples),
    "District": np.random.choice(districts, n_samples),
    "Rainfall_Index_mm": np.round(np.random.exponential(scale=10.0, size=n_samples), 2),
    "Mandi_Arrival_Tonnes": np.round(np.random.uniform(10.0, 150.0, size=n_samples), 2)
}

df = pd.DataFrame(data)

base_prices = {"Wheat": 2275, "Paddy": 2183, "Maize": 2090, "Mustard": 5650, "Apple": 7500}
df["Modal_Price"] = df.apply(
    lambda row: round(
        base_prices[row["Commodity"]] 
        - (row["Mandi_Arrival_Tonnes"] * 1.5) 
        + (row["Rainfall_Index_mm"] * 3.2) 
        + np.random.normal(0, 45), 2
    ), 
    axis=1
)

output_path = "data/mandi_data.csv"
df.to_csv(output_path, index=False)
print(f"✅ Mandi dataset generated successfully: {output_path} ({len(df)} rows)")
'@ | Out-File -FilePath "generate_data.py" -Encoding utf8