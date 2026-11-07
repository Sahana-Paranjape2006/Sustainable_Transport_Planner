
from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "Processed" / "crowd"

file = DATA / "crowd_station_hourly_processed.csv"
df = pd.read_csv(file)

print("\n===== RECORD PRESENCE BY HOUR =====")

for hour in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
    subset = df[df["Hour"] == hour]

    print(f"\nHour: {hour}")
    print("Total records:", len(subset))
    print(
        "Entry record present:",
        subset["Entry_Record_Present"].value_counts().to_dict()
    )
    print(
        "Exit record present:",
        subset["Exit_Record_Present"].value_counts().to_dict()
    )
    print(
        "Zero activity records:",
        (subset["Total_Activity"] == 0).sum()
    )
    print(
        "Total entry ridership:",
        subset["Entry_Ridership"].sum()
    )
    print(
        "Total exit ridership:",
        subset["Exit_Ridership"].sum()
    )

print("\n===== SAMPLE RECORDS FOR HOURS 1–3 =====")

columns = [
    "Date",
    "Hour",
    "Station_ID",
    "Station",
    "Entry_Ridership",
    "Exit_Ridership",
    "Entry_Record_Present",
    "Exit_Record_Present",
    "Total_Activity",
    "Crowd_Level"
]

print(
    df[df["Hour"].isin([1, 2, 3])]
    [columns]
    .head(15)
    .to_string(index=False)
)

print("\n===== CHECK COMPLETED =====")
