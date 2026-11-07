
import pandas as pd
from pathlib import Path

raw = Path(r"C:\mini_project\crowd_data_raw")

entry = pd.read_csv(
    raw / "station-hourly.csv" / "station-hourly.csv",
    sep=";"
)

exits = pd.read_csv(
    raw / "station-hourly-exits.csv" / "station-hourly-exits.csv",
    sep=";"
)

keys = ["Date", "Hour", "Station"]

missing = (
    exits[keys]
    .drop_duplicates()
    .merge(
        entry[keys].drop_duplicates(),
        on=keys,
        how="left",
        indicator=True
    )
)

missing = missing[missing["_merge"] == "left_only"]

print("Total unmatched station-hour records:", len(missing))
print("\nMissing records per station:")
print(missing.groupby("Station").size().sort_values(ascending=False).to_string())

print("\nMissing records per date:")
print(missing.groupby("Date").size().to_string())

print("\nCheck completed. No source files were modified.")
