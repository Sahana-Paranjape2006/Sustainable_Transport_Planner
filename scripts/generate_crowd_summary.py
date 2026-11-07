
from pathlib import Path
import pandas as pd

input_file = Path(
    "data/Processed/crowd/crowd_station_hourly_processed.csv"
)
output_dir = Path("data/Processed/crowd")
output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_file)

# 1. Overall dataset summary
overall = pd.DataFrame([{
    "Total_Records": len(df),
    "Unique_Stations": df["Station_ID"].nunique(),
    "Mean_Activity": df["Total_Activity"].mean(),
    "Median_Activity": df["Total_Activity"].median(),
    "Maximum_Activity": df["Total_Activity"].max(),
    "Missing_Entry_Records": (~df["Entry_Record_Present"]).sum(),
    "Missing_Exit_Records": (~df["Exit_Record_Present"]).sum(),
    "Zero_Activity_Records": (df["Total_Activity"] == 0).sum(),
    "Low_Records": (df["Crowd_Level"] == "Low").sum(),
    "Medium_Records": (df["Crowd_Level"] == "Medium").sum(),
    "High_Records": (df["Crowd_Level"] == "High").sum(),
}])

overall.to_csv(
    output_dir / "crowd_analysis_summary.csv", index=False
)

# 2. Hourly activity summary
hourly = (
    df.groupby("Hour")
      .agg(
          Average_Activity=("Total_Activity", "mean"),
          Median_Activity=("Total_Activity", "median"),
          Maximum_Activity=("Total_Activity", "max"),
          Record_Count=("Total_Activity", "size"),
      )
      .reset_index()
      .sort_values("Hour")
)

hourly.to_csv(
    output_dir / "crowd_hourly_analysis.csv", index=False
)

# 3. Station activity summary
stations = (
    df.groupby(["Station_ID", "Station"])
      .agg(
          Average_Activity=("Total_Activity", "mean"),
          Maximum_Activity=("Total_Activity", "max"),
          Record_Count=("Total_Activity", "size"),
          Missing_Entry_Records=("Entry_Record_Present",
                                 lambda x: (~x).sum()),
      )
      .reset_index()
      .sort_values("Average_Activity", ascending=False)
)

stations.to_csv(
    output_dir / "crowd_station_analysis.csv", index=False
)

print("Crowd analysis files generated:")
print(output_dir / "crowd_analysis_summary.csv")
print(output_dir / "crowd_hourly_analysis.csv")
print(output_dir / "crowd_station_analysis.csv")
print("\nTop 5 stations:")
print(stations.head(5).to_string(index=False))
