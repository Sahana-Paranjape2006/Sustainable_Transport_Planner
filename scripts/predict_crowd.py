
from pathlib import Path

import joblib
import pandas as pd


# 1. Define paths
PROJECT = Path(__file__).resolve().parent.parent

MODEL_FILE = PROJECT / "models" / "crowd" / "crowd_model.pkl"
ENCODER_FILE = PROJECT / "models" / "crowd" / "station_encoder.pkl"


# 2. Load the saved model and station encoder
model = joblib.load(MODEL_FILE)
station_encoder = joblib.load(ENCODER_FILE)


# 3. Define the prediction function
def predict_crowd(station, date, hour):
    """
    Predict crowd level for a station on a date and hour.

    hour must be an integer from 0 to 23.
    date must use YYYY-MM-DD format.
    """

    # Check hour
    if not isinstance(hour, int) or not 0 <= hour <= 23:
        raise ValueError("Hour must be an integer from 0 to 23.")

    # Convert date
    date = pd.to_datetime(date, errors="raise")

    # Check whether station exists in the training data
    if station not in station_encoder.classes_:
        raise ValueError(
            f"Unknown station: {station}. "
            "Use a station name from the training dataset."
        )

    # Convert station name into its trained numeric code
    station_code = station_encoder.transform([station])[0]

    # Extract date features
    day_of_week = date.dayofweek
    month = date.month

    # Prepare model input in the same feature order as training
    input_data = pd.DataFrame(
        [[station_code, hour, day_of_week, month]],
        columns=[
            "Station_Code",
            "Hour",
            "Day_Of_Week",
            "Month",
        ],
    )

    # Predict crowd level
    predicted_level = model.predict(input_data)[0]

    # Return result
    return {
        "station": station,
        "date": date.strftime("%Y-%m-%d"),
        "hour": hour,
        "predicted_crowd_level": predicted_level,
    }


# 4. Test the function
if __name__ == "__main__":
    result = predict_crowd(
        station="Nadaprabhu Kempegowda Station, Majestic",
        date="2025-09-30",
        hour=18,
    )

    print("\n===== CROWD PREDICTION =====")
    for key, value in result.items():
        print(f"{key}: {value}")
