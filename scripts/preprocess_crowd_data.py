
from pathlib import Path
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT = Path(__file__).resolve().parent.parent

DATA = PROJECT / "data"
RAW = DATA / "raw" / "crowd"
OUTPUT = DATA / "Processed" / "crowd"

OUTPUT.mkdir(parents=True, exist_ok=True)

entry_file = RAW / "station-hourly.csv"
exit_file = RAW / "station-hourly-exits.csv"
mapping_file = OUTPUT / "station_mapping.csv"

output_file = OUTPUT / "crowd_station_hourly_processed_test.csv"


# ============================================================
# 2. CHECK INPUT FILES
# ============================================================

for file_path in [entry_file, exit_file, mapping_file]:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}"
        )

# Never overwrite an existing test output.
if output_file.exists():
    raise FileExistsError(
        f"Output already exists: {output_file}\n"
        "Existing data was not overwritten.\n"
        "Back up or rename the existing test output before rerunning."
    )


# ============================================================
# 3. LOAD RAW DATASETS AND STATION MAPPING
# ============================================================

entry = pd.read_csv(entry_file, sep=";")
exits = pd.read_csv(exit_file, sep=";")
mapping = pd.read_csv(mapping_file, dtype=str)

required_raw_columns = {"Date", "Hour", "Station", "Ridership"}

for dataset_name, dataset in [
    ("Entry dataset", entry),
    ("Exit dataset", exits),
]:
    missing_columns = required_raw_columns - set(dataset.columns)

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing columns: "
            f"{sorted(missing_columns)}"
        )

required_mapping_columns = {"Station_ID", "Station"}

if not required_mapping_columns.issubset(mapping.columns):
    raise ValueError(
        "Station mapping must contain columns "
        "'Station_ID' and 'Station'."
    )


# ============================================================
# 4. STANDARDIZE AND VALIDATE STATION MAPPING
# ============================================================

mapping = mapping.rename(
    columns={
        "Station_ID": "code",
        "Station": "name",
    }
)

mapping["code"] = mapping["code"].astype("string").str.strip()
mapping["name"] = mapping["name"].astype("string").str.strip()

if mapping[["code", "name"]].isna().any().any():
    raise ValueError(
        "Station mapping contains missing station IDs or names."
    )

if mapping["code"].eq("").any() or mapping["name"].eq("").any():
    raise ValueError(
        "Station mapping contains empty station IDs or names."
    )

if mapping["name"].duplicated().any():
    duplicate_names = mapping.loc[
        mapping["name"].duplicated(keep=False), "name"
    ].unique()

    raise ValueError(
        "Duplicate station names in mapping: "
        f"{duplicate_names.tolist()}"
    )

if mapping["code"].duplicated().any():
    duplicate_codes = mapping.loc[
        mapping["code"].duplicated(keep=False), "code"
    ].unique()

    raise ValueError(
        "Duplicate station IDs in mapping: "
        f"{duplicate_codes.tolist()}"
    )


# ============================================================
# 5. STANDARDIZE RAW DATA
# ============================================================

def prepare_ridership_data(dataset, dataset_name):
    """Standardize raw columns and validate station-hour records."""

    df = dataset[
        ["Date", "Hour", "Station", "Ridership"]
    ].copy()

    # Standardize station names.
    df["Station"] = df["Station"].astype("string").str.strip()

    # Parse dates and numeric values.
    df["Date"] = pd.to_datetime(
        df["Date"], errors="coerce"
    ).dt.normalize()

    df["Hour"] = pd.to_numeric(
        df["Hour"], errors="coerce"
    )

    df["Ridership"] = pd.to_numeric(
        df["Ridership"], errors="coerce"
    )

    # Reject invalid dates, hours, or station names.
    if df["Date"].isna().any():
        raise ValueError(
            f"{dataset_name} contains invalid or missing dates."
        )

    if df["Hour"].isna().any():
        raise ValueError(
            f"{dataset_name} contains invalid or missing hours."
        )

    if not df["Hour"].between(0, 23).all():
        raise ValueError(
            f"{dataset_name} contains hours outside 0–23."
        )

    if not (df["Hour"] % 1 == 0).all():
        raise ValueError(
            f"{dataset_name} contains non-integer hours."
        )

    df["Hour"] = df["Hour"].astype(int)

    if df["Station"].isna().any() or df["Station"].eq("").any():
        raise ValueError(
            f"{dataset_name} contains missing station names."
        )

    if df["Ridership"].isna().any():
        raise ValueError(
            f"{dataset_name} contains missing or non-numeric "
            "ridership values."
        )

    if (df["Ridership"] < 0).any():
        raise ValueError(
            f"{dataset_name} contains negative ridership values."
        )

    # Each dataset should have at most one record per station-hour.
    duplicate_mask = df.duplicated(
        subset=["Date", "Hour", "Station"],
        keep=False
    )

    if duplicate_mask.any():
        examples = df.loc[
            duplicate_mask, ["Date", "Hour", "Station"]
        ].head(10)

        raise ValueError(
            f"{dataset_name} contains duplicate station-hour keys.\n"
            f"Examples:\n{examples.to_string(index=False)}"
        )

    return df


entry = prepare_ridership_data(entry, "Entry dataset")
exits = prepare_ridership_data(exits, "Exit dataset")


# ============================================================
# 6. CHECK THAT ALL RAW STATIONS HAVE A MAPPING
# ============================================================

known_stations = set(mapping["name"].dropna())

raw_stations = (
    set(entry["Station"].dropna())
    | set(exits["Station"].dropna())
)

unmapped_stations = sorted(raw_stations - known_stations)

if unmapped_stations:
    raise ValueError(
        "The following raw station names are missing from "
        f"station_mapping.csv: {unmapped_stations}"
    )


# ============================================================
# 7. RENAME RIDERSHIP COLUMNS
# ============================================================

entry = entry.rename(
    columns={"Ridership": "Entry_Ridership"}
)

exits = exits.rename(
    columns={"Ridership": "Exit_Ridership"}
)


# ============================================================
# 8. MERGE ENTRY AND EXIT DATA
# ============================================================

keys = ["Date", "Hour", "Station"]

# Outer merge retains records present in either dataset.
df = entry.merge(
    exits,
    on=keys,
    how="outer",
    indicator=True,
    validate="one_to_one"
)

# Preserve the original record-presence information.
df["Entry_Record_Present"] = df["_merge"].isin(
    ["left_only", "both"]
)

df["Exit_Record_Present"] = df["_merge"].isin(
    ["right_only", "both"]
)

df = df.drop(columns=["_merge"])

# A record is complete only when both source records exist.
df["Crowd_Data_Complete"] = (
    df["Entry_Record_Present"]
    & df["Exit_Record_Present"]
)


# ============================================================
# 9. HANDLE MISSING RIDERSHIP WITHOUT MISLABELING
# ============================================================

# Keep the presence flags above before filling missing values.
# Zero is used as a placeholder for arithmetic/display only.
# Incomplete rows will not receive a crowd label.

df["Entry_Ridership"] = df["Entry_Ridership"].fillna(0)
df["Exit_Ridership"] = df["Exit_Ridership"].fillna(0)


# ============================================================
# 10. ADD STATION IDs
# ============================================================

df = df.merge(
    mapping.rename(
        columns={
            "code": "Station_ID",
            "name": "Station",
        }
    ),
    on="Station",
    how="left",
    validate="many_to_one"
)

if df["Station_ID"].isna().any():
    unknown = df.loc[
        df["Station_ID"].isna(), "Station"
    ].unique()

    raise ValueError(
        f"Unmapped station names found: {unknown.tolist()}"
    )


# ============================================================
# 11. CALCULATE TOTAL ACTIVITY
# ============================================================

df["Total_Activity"] = (
    df["Entry_Ridership"] + df["Exit_Ridership"]
)

# Important:
# For incomplete rows, Total_Activity is only a partial total.
# It must not be interpreted as the true total ridership.


# ============================================================
# 12. ASSIGN CROWD LEVELS
# ============================================================

# These are the existing provisional thresholds:
# Low:    0–126
# Medium: 127–776
# High:   777 and above

df["Crowd_Level"] = pd.cut(
    df["Total_Activity"],
    bins=[-1, 126, 776, float("inf")],
    labels=["Low", "Medium", "High"]
).astype("string")

# Remove crowd labels from incomplete records.
df.loc[
    ~df["Crowd_Data_Complete"],
    "Crowd_Level"
] = pd.NA


# ============================================================
# 13. FORMAT AND SORT OUTPUT
# ============================================================

df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
df["Hour"] = df["Hour"].astype(int)

columns = [
    "Date",
    "Hour",
    "Station_ID",
    "Station",
    "Entry_Ridership",
    "Exit_Ridership",
    "Entry_Record_Present",
    "Exit_Record_Present",
    "Crowd_Data_Complete",
    "Total_Activity",
    "Crowd_Level",
]

df = df[columns].sort_values(
    ["Date", "Hour", "Station_ID"]
).reset_index(drop=True)


# ============================================================
# 14. FINAL VALIDATION BEFORE SAVING
# ============================================================

if df.duplicated(
    subset=["Date", "Hour", "Station_ID"]
).any():
    raise ValueError(
        "Duplicate station-hour records found after processing."
    )

if df["Station_ID"].isna().any():
    raise ValueError(
        "Missing station IDs found in the final dataset."
    )

if df["Total_Activity"].isna().any():
    raise ValueError(
        "Missing total activity values found in the final dataset."
    )

# Incomplete rows must not have crowd labels.
incorrect_labels = (
    ~df["Crowd_Data_Complete"]
) & df["Crowd_Level"].notna()

if incorrect_labels.any():
    raise ValueError(
        "Incomplete records incorrectly have crowd labels."
    )

# Complete rows must have crowd labels.
missing_complete_labels = (
    df["Crowd_Data_Complete"]
    & df["Crowd_Level"].isna()
)

if missing_complete_labels.any():
    raise ValueError(
        "Some complete records do not have crowd labels."
    )

# Verify record-presence flags agree with completeness.
expected_complete = (
    df["Entry_Record_Present"]
    & df["Exit_Record_Present"]
)

if not df["Crowd_Data_Complete"].equals(expected_complete):
    raise ValueError(
        "Crowd_Data_Complete does not match record-presence flags."
    )


# ============================================================
# 15. SAVE WITHOUT OVERWRITING EXISTING DATA
# ============================================================

# Recheck immediately before writing.
if output_file.exists():
    raise FileExistsError(
        f"Output already exists: {output_file}\n"
        "Existing data was not overwritten. "
        "Back up or rename it before rerunning."
    )

df.to_csv(output_file, index=False)


# ============================================================
# 16. PRINT PREPROCESSING SUMMARY
# ============================================================

print("\n===== CROWD PREPROCESSING COMPLETE =====")

print("Output:", output_file)
print("Rows:", len(df))
print("Stations:", df["Station_ID"].nunique())
print("Date range:", df["Date"].min(), "to", df["Date"].max())

print(
    "Missing entry records:",
    int((~df["Entry_Record_Present"]).sum())
)

print(
    "Missing exit records:",
    int((~df["Exit_Record_Present"]).sum())
)

print(
    "Complete records:",
    int(df["Crowd_Data_Complete"].sum())
)

print(
    "Incomplete records:",
    int((~df["Crowd_Data_Complete"]).sum())
)

print("\nCrowd-level counts (including missing labels):")
print(df["Crowd_Level"].value_counts(dropna=False))

print("\nRecord-presence combinations:")
print(
    df[
        ["Entry_Record_Present", "Exit_Record_Present"]
    ].value_counts(dropna=False)
)

print("\nPreprocessing finished successfully.")
