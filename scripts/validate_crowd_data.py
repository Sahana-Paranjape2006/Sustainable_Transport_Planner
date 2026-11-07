
from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA_FILE = (
    PROJECT / "data" / "Processed" / "crowd"
    / "crowd_station_hourly_processed_test.csv"
)

df = pd.read_csv(DATA_FILE)

print("\n===== CROWD DATA VALIDATION =====")

# 1. Check required columns
required_columns = [
    "Date", "Hour", "Station_ID", "Station",
    "Entry_Ridership", "Exit_Ridership",
    "Entry_Record_Present", "Exit_Record_Present",
    "Total_Activity", "Crowd_Level"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

print("Missing columns:", missing_columns or "None")

# 2. Check duplicate station-hour records
duplicates = df.duplicated(
    subset=["Date", "Hour", "Station_ID"]
).sum()
print("Duplicate station-hour records:", duplicates)

# 3. Check total activity calculation
expected_total = df["Entry_Ridership"] + df["Exit_Ridership"]
incorrect_totals = (df["Total_Activity"] - expected_total).abs().gt(0.000001).sum()
print("Incorrect total activity values:", incorrect_totals)

# 4. Check hour values
invalid_hours = (~df["Hour"].between(0, 23)).sum()
print("Invalid hour values:", invalid_hours)

# 5. Check missing values in important fields
print("\nMissing values:")
print(df[required_columns].isna().sum())

# 6. Check crowd-level categories
print("\nCrowd-level counts:")
print(df["Crowd_Level"].value_counts(dropna=False))

# 7. Check record-presence flags
print("\nRecord-presence combinations:")
print(
    df.groupby(
        ["Entry_Record_Present", "Exit_Record_Present"],
        dropna=False
    ).size()
)

print("\n===== VALIDATION FINISHED =====")

# 8. Examine total activity distribution
print("\n===== TOTAL ACTIVITY STATISTICS =====")
print(df["Total_Activity"].describe(
    percentiles=[0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
))

print("\n===== ACTIVITY BY CURRENT CROWD LEVEL =====")
print(
    df.groupby("Crowd_Level", observed=False)["Total_Activity"]
    .agg(["count", "min", "median", "mean", "max"])
)

print("\n===== BUSIEST STATION-HOUR RECORDS =====")
print(
    df.sort_values("Total_Activity", ascending=False)[
        ["Date", "Hour", "Station", "Total_Activity", "Crowd_Level"]
    ].head(10).to_string(index=False)
)

print("\n===== AVERAGE ACTIVITY BY HOUR =====")
print(
    df.groupby("Hour")["Total_Activity"]
    .agg(["mean", "median", "max"])
    .round(2)
    .to_string()
)

print("\n===== ZERO-ACTIVITY CHECK =====")

print(
    "Zero total activity records:",
    (df["Total_Activity"] == 0).sum()
)

print(
    "Zero activity percentage:",
    round((df["Total_Activity"] == 0).mean() * 100, 2),
    "%"
)

print("\n===== RECORD PRESENCE BY HOUR =====")

print(
    df.groupby("Hour")[
        ["Entry_Record_Present", "Exit_Record_Present"]
    ].mean().round(3).to_string()
)

print("\n===== ZERO-ACTIVITY BREAKDOWN =====")

zero_activity = df[df["Total_Activity"] == 0]

observed_zero = zero_activity[
    zero_activity["Entry_Record_Present"]
    & zero_activity["Exit_Record_Present"]
]

incomplete_zero = zero_activity[
    ~zero_activity["Entry_Record_Present"]
    | ~zero_activity["Exit_Record_Present"]
]

print("Total zero-activity records:", len(zero_activity))
print("Zero with both records present:", len(observed_zero))
print("Zero with incomplete records:", len(incomplete_zero))

print("\n===== ZERO ACTIVITY BY HOUR =====")

print(
    zero_activity.groupby("Hour").size()
    .reindex(range(24), fill_value=0)
    .to_string()
)

print("\n===== ZERO ACTIVITY BY STATION =====")

station_zero = (
    df.assign(Is_Zero=df["Total_Activity"] == 0)
    .groupby("Station")
    .agg(
        Total_Records=("Total_Activity", "size"),
        Zero_Records=("Is_Zero", "sum"),
        Average_Activity=("Total_Activity", "mean")
    )
)

station_zero["Zero_Percentage"] = (
    station_zero["Zero_Records"]
    / station_zero["Total_Records"] * 100
).round(2)

print(
    station_zero.sort_values(
        "Zero_Percentage", ascending=False
    ).head(15).to_string()
)

print("\n===== INCOMPLETE ENTRY RECORDS BY STATION =====")

print(
    df.loc[~df["Entry_Record_Present"]]
    .groupby("Station")
    .size()
    .sort_values(ascending=False)
    .head(15)
    .to_string()
)

print("\n===== RAW ENTRY AND EXIT COVERAGE =====")

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw" / "crowd"

entry_raw = pd.read_csv(RAW / "station-hourly.csv", sep=";")
exit_raw = pd.read_csv(RAW / "station-hourly-exits.csv", sep=";")

for label, raw_df in [("Entry", entry_raw), ("Exit", exit_raw)]:
    print(f"\n{label} dataset")
    print("Rows:", len(raw_df))
    print("Columns:", raw_df.columns.tolist())
    print("Date range:", raw_df["Date"].min(), "to", raw_df["Date"].max())
    print("Unique stations:", raw_df["Station"].nunique())
    print("Duplicate station-hour keys:", raw_df.duplicated(
        ["Date", "Hour", "Station"]
    ).sum())

print("\n===== RAW ENTRY COVERAGE FOR SELECTED STATIONS =====")

selected = [
    "BTM Layout",
    "Beratena Agrahara",
    "Biocon Hebbagodi",
    "Bommanahalli",
    "Central Silk Board",
]

for station in selected:
    entry_rows = entry_raw[entry_raw["Station"] == station]
    exit_rows = exit_raw[exit_raw["Station"] == station]

    print(
        f"{station}: "
        f"entry rows={len(entry_rows)}, "
        f"exit rows={len(exit_rows)}"
    )

print("\n===== MISSING ENTRY RECORDS BY HOUR =====")

expected_hours = pd.MultiIndex.from_product(
    [
        pd.date_range("2025-08-01", "2025-09-30", freq="D")
            .strftime("%Y-%m-%d"),
        range(24),
        entry_raw["Station"].unique()
    ],
    names=["Date", "Hour", "Station"]
)

actual_entry_keys = pd.MultiIndex.from_frame(
    entry_raw[["Date", "Hour", "Station"]].assign(
        Hour=lambda x: pd.to_numeric(x["Hour"])
    ).assign(
        Date=lambda x: pd.to_datetime(x["Date"]).dt.strftime("%Y-%m-%d")
    )
)

missing_keys = expected_hours.difference(actual_entry_keys)

missing_df = missing_keys.to_frame(index=False)

print("Total missing station-hour records:", len(missing_df))
print("\nMissing records by hour:")
print(
    missing_df.groupby("Hour").size()
    .reindex(range(24), fill_value=0)
    .to_string()
)

print("\nMissing records by date (first 15 dates):")
print(
    missing_df.groupby("Date").size()
    .sort_values(ascending=False)
    .head(15)
    .to_string()
)

print("\n===== ENTRY COVERAGE CROSS-CHECK =====")

entry_keys = entry_raw[["Date", "Hour", "Station"]].copy()
exit_keys = exit_raw[["Date", "Hour", "Station"]].copy()

for keys in [entry_keys, exit_keys]:
    keys["Date"] = pd.to_datetime(keys["Date"]).dt.strftime("%Y-%m-%d")
    keys["Hour"] = pd.to_numeric(keys["Hour"], errors="coerce")
    keys["Station"] = keys["Station"].astype(str).str.strip()

entry_key_set = set(map(tuple, entry_keys.to_numpy()))
exit_key_set = set(map(tuple, exit_keys.to_numpy()))

missing_from_entry = exit_key_set - entry_key_set

print("Unique entry station-hour keys:", len(entry_key_set))
print("Unique exit station-hour keys:", len(exit_key_set))
print("Exit keys with no matching entry key:", len(missing_from_entry))

missing_from_entry_df = pd.DataFrame(
    list(missing_from_entry),
    columns=["Date", "Hour", "Station"]
)

print("\nMissing entry records by date (top 15):")
print(
    missing_from_entry_df.groupby("Date").size()
    .sort_values(ascending=False)
    .head(15)
    .to_string()
)

print("\nMissing entry records by station (top 15):")
print(
    missing_from_entry_df.groupby("Station").size()
    .sort_values(ascending=False)
    .head(15)
    .to_string()
)

print("\n===== FULL ENTRY DATA GAP SUMMARY =====")

print("\nMissing entry records by date:")
print(
    missing_from_entry_df.groupby("Date").size()
    .reindex(
        pd.date_range("2025-08-01", "2025-09-30")
        .strftime("%Y-%m-%d"),
        fill_value=0
    )
    .to_string()
)

print("\nMissing entry records by station:")
print(
    missing_from_entry_df.groupby("Station").size()
    .sort_values(ascending=False)
    .to_string()
)

print("\n===== FULL ENTRY DATA GAP SUMMARY =====")

print("\nMissing entry records by date:")
print(
    missing_from_entry_df.groupby("Date").size()
    .reindex(
        pd.date_range("2025-08-01", "2025-09-30")
        .strftime("%Y-%m-%d"),
        fill_value=0
    )
    .to_string()
)

print("\nMissing entry records by station:")
print(
    missing_from_entry_df.groupby("Station").size()
    .sort_values(ascending=False)
    .to_string()
)
