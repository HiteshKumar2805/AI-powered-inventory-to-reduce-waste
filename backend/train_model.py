import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

# Load CSV
df = pd.read_csv(r"C:\Users\Admin\OneDrive\Desktop\VScode\ai-inventory-optimizer\backend\inventory_data.csv")

# Preview data
print("📊 Columns:", df.columns)

# Define your features and target
features = ['inventory', 'sales']
target = 'sales'  # TEMP: Predicting sales as proxy if 'demand' not available

# Train model
X = df[features]
y = df[target]

model = RandomForestRegressor()
model.fit(X, y)

# Save model
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/inventory_model.pkl")
print("✅ Model saved to models/inventory_model.pkl")
