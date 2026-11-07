
from pathlib import Path

ROOT = Path(r"C:\mini_project")

extensions = {".csv", ".xlsx", ".xls"}

print("Searching for data files...\n")

for file in ROOT.rglob("*"):
    if file.is_file() and file.suffix.lower() in extensions:
        if ".git" not in file.parts:
            print(file)

print("\nSearch completed.")
