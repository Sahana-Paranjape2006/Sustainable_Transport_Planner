
from pathlib import Path
import pandas as pd

# Team repository location
PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "Processed" / "crowd"

hourly_file = DATA / "crowd_station_hourly_processed.csv"
mapping_file = DATA / "station_mapping.csv"
station_file = DATA / "crowd_station_summary.csv"
hourly_summary_file = DATA / "crowd_hourly_summary.csv"

# Load datasets
hourly = pd.read_csv(hourly_file)
mapping = pd.read_csv(mapping_file)
stations = pd.read_csv(station_file)
hour_summary = pd.read_csv(hourly_summary_file)

print("\n========== CROWD DATA VALIDATION ==========")

# 1. Dataset size and date range
hourly["Date"] = pd.to_datetime(
    hourly["Date"], errors="coerce"
)

print("\n1. DATASET OVERVIEW")
print("Hourly records:", len(hourly))
print("Unique stations:", hourly["Station_ID"].nunique())
print("Date range:", hourly["Date"].min(), "to",
      hourly["Date"].max())
print("Invalid dates:", hourly["Date"].isna().sum())

# 2. Check duplicate station-hour records
print("\n2. DUPLICATE CHECK")
key = ["Date", "Hour", "Station_ID"]
duplicates = hourly.duplicated(subset=key).sum()
print("Duplicate station-hour records:", duplicates)

# 3. Check crowd-level distribution
print("\n3. CROWD LEVEL DISTRIBUTION")
print(hourly["Crowd_Level"].value_counts(dropna=False))

print("\nCrowd level percentages:")
print(
    (hourly["Crowd_Level"].value_counts(
        normalize=True, dropna=False
    ) * 100).round(2)
)

# 4. Check total activity calculation
print("\n4. ACTIVITY CALCULATION")
expected = (
    hourly["Entry_Ridership"] +
    hourly["Exit_Ridership"]
)
difference = (
    hourly["Total_Activity"] - expected
).abs()

print("Rows where total activity differs from entries + exits:",
      (difference > 0.01).sum())

print("Negative entry values:",
      (hourly["Entry_Ridership"] < 0).sum())
print("Negative exit values:",
      (hourly["Exit_Ridership"] < 0).sum())
print("Negative total activity:",
      (hourly["Total_Activity"] < 0).sum())

# 5. Check station mapping
print("\n5. STATION MAPPING")
print("Stations in mapping:", mapping["Station_ID"].nunique())
print("Stations in hourly data:", hourly["Station_ID"].nunique())

unmapped = set(hourly["Station_ID"]) - set(mapping["Station_ID"])
print("Station IDs missing from mapping:", len(unmapped))
if unmapped:
    print("Unmapped IDs:", sorted(unmapped))

# Check whether names agree for matching station IDs
name_check = hourly[["Station_ID", "Station"]].drop_duplicates()
name_check = name_check.merge(
    mapping,
    on="Station_ID",
    how="left",
    suffixes=("_hourly", "_mapping")
)
name_mismatch = (
    name_check["Station_hourly"].str.strip()
    != name_check["Station_mapping"].str.strip()
)
print("Station name mismatches:", name_mismatch.sum())

# 6. Check hourly summary
print("\n6. HOURLY SUMMARY")
print("Number of hour rows:", len(hour_summary))
print("Hour values:", sorted(hour_summary["Hour"].unique()))
print("Lowest activity hours:")
print(hour_summary.nsmallest(
    5, "Total_Activity_All_Stations"
).to_string(index=False))

# 7. Check summary station count
print("\n7. SUMMARY CONSISTENCY")
print("Rows in station summary:", len(stations))
print("Unique summary stations:", stations["Station_ID"].nunique())

print("\nValidation checks completed.")
print("Review any non-zero errors before integration.")
