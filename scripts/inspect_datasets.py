
from pathlib import Path
import pandas as pd

# Team repository root
PROJECT = Path(__file__).resolve().parent.parent

# Your processed crowd datasets
DATA_FOLDER = PROJECT / "data" / "Processed" / "crowd"

if not DATA_FOLDER.exists():
    raise FileNotFoundError(
        f"Crowd dataset folder not found: {DATA_FOLDER}"
    )

files = sorted(DATA_FOLDER.glob("*.csv"))

if not files:
    print("No CSV files found in:", DATA_FOLDER)

for file in files:
    print("\n" + "=" * 60)
    print("FILE:", file.name)

    try:
        df = pd.read_csv(file)

        print("Rows:", len(df))
        print("Columns:", len(df.columns))
        print("\nColumn names:")
        print(df.columns.tolist())

        print("\nFirst 5 rows:")
        print(df.head().to_string(index=False))

        print("\nMissing values:")
        print(df.isnull().sum().to_string())

        print("\nData types:")
        print(df.dtypes.to_string())

    except Exception as error:
        print("Error reading file:", error)
