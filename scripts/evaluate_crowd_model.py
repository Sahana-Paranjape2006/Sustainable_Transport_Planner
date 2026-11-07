
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "Processed"
    / "crowd"
    / "crowd_station_hourly_processed_test.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "crowd"
    / "crowd_model.pkl"
)

ENCODER_PATH = (
    PROJECT_ROOT
    / "models"
    / "crowd"
    / "station_encoder.pkl"
)

from scripts.predict_crowd import model, station_encoder


def main():
    df = pd.read_csv(DATA_PATH)

    # Use only complete records with valid crowd labels
    df = df[
        (df["Crowd_Data_Complete"] == True)
        & (df["Crowd_Level"].notna())
    ].copy()

    # Prepare the same features used during training
    df["Date"] = pd.to_datetime(df["Date"])
    df["Station_Encoded"] = station_encoder.transform(
        df["Station"].str.strip()
    )

    X = pd.DataFrame({
        "Station_Code": df["Station_Encoded"],
        "Hour": df["Hour"],
        "Day_Of_Week": df["Date"].dt.dayofweek,
        "Month": df["Date"].dt.month,
    })

    y_actual = df["Crowd_Level"]
    y_predicted = model.predict(X)

    print("\n===== CROWD MODEL EVALUATION =====")
    print("Total records evaluated:", len(df))
    print(
        "Accuracy:",
        round(accuracy_score(y_actual, y_predicted) * 100, 2),
        "%",
    )

    print("\n===== CLASSIFICATION REPORT =====")
    print(
        classification_report(
            y_actual,
            y_predicted,
            labels=["Low", "Medium", "High"],
            zero_division=0,
        )
    )

    print("\n===== CONFUSION MATRIX =====")
    print("Rows = Actual | Columns = Predicted")
    print(
        pd.DataFrame(
            confusion_matrix(
                y_actual,
                y_predicted,
                labels=["Low", "Medium", "High"],
            ),
            index=["Actual Low", "Actual Medium", "Actual High"],
            columns=["Predicted Low", "Predicted Medium", "Predicted High"],
        )
    )


if __name__ == "__main__":
    main()
