
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
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


def main():
    df = pd.read_csv(DATA_PATH)

    df = df[
        (df["Crowd_Data_Complete"] == True)
        & (df["Crowd_Level"].notna())
    ].copy()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Station"] = df["Station"].str.strip()

    # Sort unique dates and reserve the last 20% for testing
    unique_dates = sorted(df["Date"].unique())
    split_index = int(len(unique_dates) * 0.8)
    split_date = unique_dates[split_index]

    train_df = df[df["Date"] < split_date].copy()
    test_df = df[df["Date"] >= split_date].copy()

    # Fit station encoder using training data only
    encoder = LabelEncoder()
    encoder.fit(train_df["Station"])

    # Ensure test stations are known to the encoder
    unknown_stations = (
        set(test_df["Station"]) - set(encoder.classes_)
    )

    if unknown_stations:
        raise ValueError(
            f"Stations missing from training data: {unknown_stations}"
        )

    def prepare_features(data):
        return pd.DataFrame({
            "Station_Code": encoder.transform(data["Station"]),
            "Hour": data["Hour"],
            "Day_Of_Week": data["Date"].dt.dayofweek,
            "Month": data["Date"].dt.month,
        })

    X_train = prepare_features(train_df)
    X_test = prepare_features(test_df)

    y_train = train_df["Crowd_Level"]
    y_test = test_df["Crowd_Level"]

    # Train a fresh model using only earlier dates
    model = RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print("\n===== TEMPORAL MODEL EVALUATION =====")
    print("Training records:", len(train_df))
    print("Testing records:", len(test_df))
    print("Training through:", train_df["Date"].max().date())
    print("Testing from:", test_df["Date"].min().date())
    print("Testing through:", test_df["Date"].max().date())

    print(
        "\nTest accuracy:",
        round(accuracy_score(y_test, predictions) * 100, 2),
        "%",
    )

    print("\n===== CLASSIFICATION REPORT =====")
    print(
        classification_report(
            y_test,
            predictions,
            labels=["Low", "Medium", "High"],
            zero_division=0,
        )
    )

    print("\n===== CONFUSION MATRIX =====")
    print(
        pd.DataFrame(
            confusion_matrix(
                y_test,
                predictions,
                labels=["Low", "Medium", "High"],
            ),
            index=["Actual Low", "Actual Medium", "Actual High"],
            columns=[
                "Predicted Low",
                "Predicted Medium",
                "Predicted High",
            ],
        )
    )


if __name__ == "__main__":
    main()
