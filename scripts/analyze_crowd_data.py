from pathlib import Path
import pandas as pd

input_file = Path(
    "data/Processed/crowd/crowd_station_hourly_processed.csv"
)

df = pd.read_csv(input_file)

print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nCrowd-level distribution:")
print(df["Crowd_Level"].value_counts(dropna=False))

print("\nActivity statistics:")
print(df["Total_Activity"].describe())

print("\nAverage activity by hour:")
print(
    df.groupby("Hour")["Total_Activity"]
      .mean()
      .sort_values(ascending=False)
)

print("\nBusiest stations by average activity:")
print(
    df.groupby("Station")["Total_Activity"]
      .mean()
      .sort_values(ascending=False)
      .head(10)
)
print("\n--- CROWD THRESHOLD VALIDATION ---")

thresholds = {
    "Low": (0, 126),
    "Medium": (127, 776),
    "High": (777, float("inf")),
}

for level, (lower, upper) in thresholds.items():
    actual = df.loc[df["Crowd_Level"] == level, "Total_Activity"]

    print(f"\n{level}")
    print("Record count:", len(actual))
    print("Minimum activity:", actual.min())
    print("Maximum activity:", actual.max())

    invalid = actual[
        (actual < lower) | (actual > upper)
    ]
    print("Records outside configured range:", len(invalid))

print("\nActual labels vs configured thresholds:")
expected = pd.Series("Medium", index=df.index)
expected.loc[df["Total_Activity"] <= 126] = "Low"
expected.loc[df["Total_Activity"] >= 777] = "High"

print("Mismatched labels:", (expected != df["Crowd_Level"]).sum())
print("\n--- DATA COMPLETENESS ---")

print("Entry record present:")
print(df["Entry_Record_Present"].value_counts(dropna=False))

print("\nExit record present:")
print(df["Exit_Record_Present"].value_counts(dropna=False))

print(
    "\nMissing entry records:",
    (~df["Entry_Record_Present"]).sum()
)

print(
    "\nMissing exit records:",
    (~df["Exit_Record_Present"]).sum()
)

print(
    "\nZero activity records:",
    (df["Total_Activity"] == 0).sum()
)

print(
    "\nDate range:",
    df["Date"].min(),
    "to",
    df["Date"].max()
)