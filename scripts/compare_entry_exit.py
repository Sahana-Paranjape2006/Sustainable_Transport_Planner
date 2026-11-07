
import pandas as pd
from pathlib import Path

raw = Path(r"C:\mini_project\crowd_data_raw")

entry_file = raw / "station-hourly.csv" / "station-hourly.csv"
exit_file = raw / "station-hourly-exits.csv" / "station-hourly-exits.csv"

entry = pd.read_csv(entry_file, sep=";", engine="python")
exits = pd.read_csv(exit_file, sep=";", engine="python")

keys = ["Date", "Hour", "Station"]

# Compare the station-hour records in both files
entry_keys = entry[keys].drop_duplicates()
exit_keys = exits[keys].drop_duplicates()

comparison = exit_keys.merge(
    entry_keys,
    on=keys,
    how="left",
    indicator=True
)

missing_entry = comparison[comparison["_merge"] == "left_only"]

print("Entry records:", len(entry))
print("Exit records:", len(exits))
print("Exit records without matching entry records:", len(missing_entry))

print("\nFirst 20 unmatched records:")
print(missing_entry[keys].head(20).to_string(index=False))

print("\nUnmatched records by date:")
print(missing_entry.groupby("Date").size().to_string())

print("\nCheck completed. Original files were not modified.")

print("\nUnmatched records by station:")
print(
    missing_entry.groupby("Station")
    .size()
    .sort_values(ascending=False)
    .to_string()
)

print("\nNumber of unmatched records by hour:")
print(
    missing_entry.groupby("Hour")
    .size()
    .sort_values(ascending=False)
    .to_string()
)

print("\nStations present in EXIT but absent from ENTRY:")
entry_stations = set(entry["Station"].dropna().unique())
exit_stations = set(exits["Station"].dropna().unique())

print(sorted(exit_stations - entry_stations))

print("\nTotal unique stations in ENTRY:", len(entry_stations))
print("Total unique stations in EXIT:", len(exit_stations))

station = "BTM Layout"

print(f"\nENTRY records for {station}:")
print(
    entry[entry["Station"] == station]
    .head(30)
    .to_string(index=False)
)

print(f"\nEXIT records for {station}:")
print(
    exits[exits["Station"] == station]
    .head(30)
    .to_string(index=False)
)

print("\nNumber of ENTRY records:", len(entry[entry["Station"] == station]))
print("Number of EXIT records:", len(exits[exits["Station"] == station]))

station = "BTM Layout"

for label, df in [("ENTRY", entry), ("EXIT", exits)]:
    station_data = df[df["Station"] == station].copy()
    dates = sorted(station_data["Date"].unique())

    print(f"\n{label} — {station}")
    print("First date:", dates[0])
    print("Last date:", dates[-1])
    print("Unique dates:", len(dates))
    print("Records per date:")
    print(station_data.groupby("Date").size().to_string())
