
from pathlib import Path
import fitz
import pdfplumber
import pandas as pd

# Project PDF location
pdf_path = Path(
    "data/Processed/crowd/bmtc/raw/CMP/"
    "Bengaluru_CMP_2019_Draft.pdf"
)

# Output folder
output_folder = Path(
    "data/Processed/crowd/bmtc/raw/CMP/extracted"
)

output_folder.mkdir(parents=True, exist_ok=True)

if not pdf_path.exists():
    print("ERROR: CMP PDF not found!")
    print("Expected location:", pdf_path.resolve())
    raise SystemExit

print("CMP PDF inspection started")

# --------------------------------
# STEP 1: Extract text page by page
# --------------------------------

pdf = fitz.open(pdf_path)

print("\nTotal PDF pages:", len(pdf))

all_text = []

keywords = [
    "boarding",
    "alighting",
    "passenger",
    "bus stop",
    "peak hour",
    "inflow",
    "outflow",
    "terminal",
    "bus travel",
    "passenger survey",
    "occupancy"
]

for page_number, page in enumerate(pdf, start=1):

    page_text = page.get_text("text")

    all_text.append(
        f"\n\n========== PAGE {page_number} ==========\n"
        + page_text
    )

    matching_keywords = [
        word for word in keywords
        if word.lower() in page_text.lower()
    ]

    if matching_keywords:
        print(
            f"Page {page_number}: "
            + ", ".join(matching_keywords)
        )

# Save complete extracted text
text_file = output_folder / "cmp_extracted_text.txt"

text_file.write_text(
    "\n".join(all_text),
    encoding="utf-8"
)

print("\nText saved:", text_file)

pdf.close()

# --------------------------------
# STEP 2: Extract PDF tables
# --------------------------------

table_count = 0

with pdfplumber.open(pdf_path) as pdf:

    for page_number, page in enumerate(pdf.pages, start=1):

        tables = page.extract_tables()

        if not tables:
            continue

        for table_number, table in enumerate(tables, start=1):

            if not table:
                continue

            df = pd.DataFrame(table)

            # Preserve extracted table without
            # assuming the first row is the header.
            output_file = output_folder / (
                f"page_{page_number}_table_{table_number}.csv"
            )

            df.to_csv(
                output_file,
                index=False,
                header=False
            )

            table_count += 1

            print("Extracted:", output_file)

print("\n========== INSPECTION COMPLETE ==========")
print("Total tables extracted:", table_count)
print("Output folder:", output_folder.resolve())
