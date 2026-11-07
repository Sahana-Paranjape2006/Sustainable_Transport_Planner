
from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "Processed" / "crowd"

file = DATA / "crowd_station_hourly_processed.csv"
df = pd.read_csv(file)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

print("\n========== DATE COVERAGE ==========")

print("Unique dates:", df["Date"].nunique())
print("First date:", df["Date"].min())
print("Last date:", df["Date"].max())

expected_dates = pd.date_range(
    df["Date"].min(), df["Date"].max(), freq="D"
)

present_dates = pd.DatetimeIndex(
    df["Date"].dropna().unique()
)

missing_dates = expected_dates.difference(present_dates)

print("Calendar dates in range:", len(expected_dates))
print("Missing dates:", len(missing_dates))
print("Missing date list:", missing_dates.strftime("%Y-%m-%d").tolist())

print("\nRecords per date:")
print(df.groupby("Date").size().value_counts().sort_index())

print("\n========== CROWD LEVEL THRESHOLDS ==========")

print("\nActivity statistics:")
print(df["Total_Activity"].describe(
    percentiles=[0.10, 0.25, 0.33, 0.50, 0.67, 0.75, 0.90]
))

print("\nCrowd-level statistics:")
print(
    df.groupby("Crowd_Level")["Total_Activity"]
    .agg(["count", "min", "median", "mean", "max"])
    .sort_values("median")
    .to_string()
)

print("\nActivity ranges for each crowd level:")
for level in ["Low", "Medium", "High"]:
    values = df.loc[
        df["Crowd_Level"] == level, "Total_Activity"
    ]
    if len(values):
        print(
            level,
            "| min:", values.min(),
            "| median:", values.median(),
            "| max:", values.max()
        )

print("\n========== HOURLY ACTIVITY CHECK ==========")

hourly = df.groupby("Hour").agg(
    Total_Activity=("Total_Activity", "sum"),
    Records=("Total_Activity", "size"),
    Zero_Activity=("Total_Activity", lambda x: (x == 0).sum())
)

print(hourly.to_string())

print("\n========== CHECK COMPLETED ==========")
