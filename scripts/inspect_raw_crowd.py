
from pathlib import Path
import pandas as pd

RAW = Path(r"C:\mini_project\crowd_data_raw")

files = {
    "ENTRY": RAW / "station-hourly.csv" / "station-hourly.csv",
    "EXIT": RAW / "station-hourly-exits.csv" / "station-hourly-exits.csv",
}

for label, file in files.items():
    print("\n" + "=" * 60)
    print(label, "FILE")
    print("Path:", file)

    try:
        # Skip malformed rows for this inspection only.
        df = pd.read_csv(
    file,
    sep=";",
    engine="python",
    on_bad_lines="warn"
)

        print("Columns:", list(df.columns))
        print("Rows successfully read:", len(df))

        if "Date" not in df.columns:
            print("Date column not found. Check the file format.")
            continue

        dates = pd.to_datetime(
            df["Date"].astype(str).str.strip(),
            format="%Y-%m-%d",
            errors="coerce"
        )

        print("Invalid dates:", dates.isna().sum())
        print("Unique dates:", dates.nunique())
        print("First date:", dates.min())
        print("Last date:", dates.max())

        expected = pd.date_range(
            dates.min(), dates.max(), freq="D"
        )

        present = pd.DatetimeIndex(dates.dropna().unique())
        missing = expected.difference(present)

        print("Calendar dates in range:", len(expected))
        print("Missing dates:", len(missing))
        print("Missing date list:",
              missing.strftime("%Y-%m-%d").tolist())

        if {"Date", "Hour", "Station"}.issubset(df.columns):
            print(
                "Duplicate Date-Hour-Station rows:",
                df.assign(Date=dates).duplicated(
                    ["Date", "Hour", "Station"]
                ).sum()
            )

    except Exception as error:
        print("Inspection failed:", repr(error))

print("\nInspection completed. Original files were not modified.")
