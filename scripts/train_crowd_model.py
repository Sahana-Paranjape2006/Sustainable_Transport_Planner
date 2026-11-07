
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib


# 1. Define project paths
PROJECT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT
    / "data"
    / "Processed"
    / "crowd"
    / "crowd_station_hourly_processed_test.csv"
)

MODEL_DIR = PROJECT / "models" / "crowd"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "crowd_model.pkl"
ENCODER_FILE = MODEL_DIR / "station_encoder.pkl"


# 2. Load processed data
df = pd.read_csv(DATA_FILE)

print("Dataset loaded:", df.shape)


# 3. Keep only records with complete entry and exit data
df = df[df["Crowd_Data_Complete"] == True].copy()

# Crowd labels must be present
df = df.dropna(subset=["Crowd_Level"])

print("Complete records available for training:", len(df))


# 4. Extract useful date and time features
df["Date"] = pd.to_datetime(df["Date"])

df["Day_Of_Week"] = df["Date"].dt.dayofweek
df["Month"] = df["Date"].dt.month

# Encode station names into numbers
station_encoder = LabelEncoder()
df["Station_Code"] = station_encoder.fit_transform(
    df["Station"].astype(str)
)

# Model inputs
feature_columns = [
    "Station_Code",
    "Hour",
    "Day_Of_Week",
    "Month",
]

X = df[feature_columns]
y = df["Crowd_Level"]


# 5. Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)


# 6. Train the model
model = RandomForestClassifier(
    n_estimators=150,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1,
)

print("\nTraining crowd prediction model...")
model.fit(X_train, y_train)


# 7. Evaluate model performance
predictions = model.predict(X_test)

print("\n===== MODEL EVALUATION =====")
print("Accuracy:", round(accuracy_score(y_test, predictions), 4))
print("\nClassification Report:")
print(classification_report(y_test, predictions, zero_division=0))


# 8. Save model and station encoder
joblib.dump(model, MODEL_FILE)
joblib.dump(station_encoder, ENCODER_FILE)

print("\n===== MODEL SAVED =====")
print("Model:", MODEL_FILE)
print("Station encoder:", ENCODER_FILE)
print("Training completed successfully.")
