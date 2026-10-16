
from pathlib import Path
import pandas as pd

# Project folders
PROJECT = Path(__file__).resolve().parent.parent
RAW = Path(r"C:\mini_project\crowd_data_raw")
OUTPUT = PROJECT / "data" / "Processed" / "crowd"

OUTPUT.mkdir(parents=True, exist_ok=True)

# Load raw datasets
entry_file = RAW / "station-hourly.csv" / "station-hourly.csv"
exit_file = RAW / "station-hourly-exits.csv" / "station-hourly-exits.csv"
mapping_file = PROJECT / "data" / "raw" / "crowd" / "station-codes.csv"

entry = pd.read_csv(entry_file, sep=";")
exits = pd.read_csv(exit_file, sep=";")
mapping = pd.read_csv(mapping_file, sep=None, engine="python")

# Load the established station mapping independently
mapping = pd.read_csv(
    OUTPUT / "station_mapping.csv",
    dtype=str
)

mapping = mapping.rename(
    columns={"Station_ID": "code", "Station": "name"}
)

mapping["code"] = mapping["code"].str.strip()
mapping["name"] = mapping["name"].str.strip()

if mapping["name"].duplicated().any():
    raise ValueError("Station mapping contains duplicate station names.")

if mapping["code"].duplicated().any():
    raise ValueError("Station mapping contains duplicate station IDs.")

# Standardize fields
for df in (entry, exits):
    df["Date"] = pd.to_datetime(
        df["Date"], format="%Y-%m-%d", errors="coerce"
    )
    df["Hour"] = pd.to_numeric(df["Hour"], errors="coerce")
    df["Station"] = df["Station"].astype("string").str.strip()
    df["Ridership"] = pd.to_numeric(
        df["Ridership"], errors="coerce"
    )

mapping["code"] = mapping["code"].astype("string").str.strip()
mapping["name"] = mapping["name"].astype("string").str.strip()

# Validate raw data before merging
for label, df in (("Entry", entry), ("Exit", exits)):
    if df[["Date", "Hour", "Station"]].isna().any().any():
        raise ValueError(f"{label} data contains invalid date/hour/station keys.")

    if df.duplicated(["Date", "Hour", "Station"]).any():
        raise ValueError(f"{label} data contains duplicate station-hour records.")

    if df["Ridership"].isna().any() or (df["Ridership"] < 0).any():
        raise ValueError(f"{label} data contains missing or negative ridership.")

if mapping["name"].duplicated().any():
    raise ValueError(
        "Station mapping has duplicate names. Resolve these before processing."
    )

# Rename ridership columns and preserve record presence
entry = entry.rename(columns={"Ridership": "Entry_Ridership"})
entry["Entry_Record_Present"] = True

exits = exits.rename(columns={"Ridership": "Exit_Ridership"})
exits["Exit_Record_Present"] = True

keys = ["Date", "Hour", "Station"]

# Outer join preserves records found in either source
df = entry.merge(
    exits,
    on=keys,
    how="outer",
    validate="one_to_one"
)

# Preserve missingness before using zero placeholders
df["Entry_Record_Present"] = (
    df["Entry_Record_Present"].fillna(False).astype(bool)
)
df["Exit_Record_Present"] = (
    df["Exit_Record_Present"].fillna(False).astype(bool)
)

df["Entry_Ridership"] = df["Entry_Ridership"].fillna(0)
df["Exit_Ridership"] = df["Exit_Ridership"].fillna(0)

# Add station IDs
df = df.merge(
    mapping.rename(columns={"code": "Station_ID", "name": "Station"}),
    on="Station",
    how="left",
    validate="many_to_one"
)

if df["Station_ID"].isna().any():
    unknown = df.loc[df["Station_ID"].isna(), "Station"].unique()
    raise ValueError(f"Unmapped station names found: {unknown.tolist()}")

# Calculate total activity
df["Total_Activity"] = (
    df["Entry_Ridership"] + df["Exit_Ridership"]
)

# Retain existing thresholds for initial compatibility
df["Crowd_Level"] = pd.cut(
    df["Total_Activity"],
    bins=[-1, 126, 776, float("inf")],
    labels=["Low", "Medium", "High"]
).astype(str)

# Format output
df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
df["Hour"] = df["Hour"].astype(int)

columns = [
    "Date", "Hour", "Station_ID", "Station",
    "Entry_Ridership", "Exit_Ridership",
    "Entry_Record_Present", "Exit_Record_Present",
    "Total_Activity", "Crowd_Level"
]

df = df[columns].sort_values(
    ["Date", "Hour", "Station_ID"]
).reset_index(drop=True)

# Save regenerated dataset
output_file = OUTPUT / "crowd_station_hourly_processed.csv"
df.to_csv(output_file, index=False)

# Print validation summary
print("\n===== CROWD PREPROCESSING COMPLETE =====")
print("Output:", output_file)
print("Rows:", len(df))
print("Stations:", df["Station_ID"].nunique())
print("Date range:", df["Date"].min(), "to", df["Date"].max())
print("Missing entry records:", (~df["Entry_Record_Present"]).sum())
print("Missing exit records:", (~df["Exit_Record_Present"]).sum())
print("\nCrowd-level counts:")
print(df["Crowd_Level"].value_counts())
print("\nRecord-presence counts:")
print(df[["Entry_Record_Present", "Exit_Record_Present"]].value_counts())
print("\nPreprocessing finished.")
