import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

os.makedirs("ml_models", exist_ok=True)

# 1. Check Dataset
data_path = "data/mandi_data.csv"
if not os.path.exists(data_path):
    print("❌ Error: data/mandi_data.csv nahi mili! Pehle generate_data.py run karo.")
    exit()

df = pd.read_csv(data_path)
df["Date"] = pd.to_datetime(df["Date"])
df["Month"] = df["Date"].dt.month
df["DayOfWeek"] = df["Date"].dt.dayofweek

# 2. Features & Target
features = [
    "Commodity",
    "District",
    "Month",
    "DayOfWeek",
    "Rainfall_Index_mm",
    "Mandi_Arrival_Tonnes",
]
target = "Modal_Price"

X = df[features]
y = df[target]

# 3. Pipeline
categorical_features = ["Commodity", "District"]
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ],
    remainder="passthrough",
)

model_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=100, random_state=42)),
    ]
)

# 4. Train Model
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42
)
print("⏳ Training Krishi Setu Price Prediction Model...")
model_pipeline.fit(X_train, y_train)

preds = model_pipeline.predict(X_test)
print(
    f"✅ Training Done! MAE: ₹{mean_absolute_error(y_test, preds):.2f} | R2: {r2_score(y_test, preds):.3f}"
)

# 5. Save Model
output_file = "ml_models/mandi_price_model.pkl"
joblib.dump(model_pipeline, output_file)
print(f"📦 Model saved successfully at: {output_file}")
