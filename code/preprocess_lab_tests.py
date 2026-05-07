#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd


SECTION_TO_LAB_TYPE = {
    "Γ": "Imaging",
    "Δ": "BioPath",
    "Ε": "Pathology",
}


def clean(value: object) -> str:
    if value is None:
        return ""
    value = str(value)
    if value.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", value.replace("\ufeff", " ")).strip()


def default_source_path(project_root: Path) -> Path:
    raw_dir = project_root / "data" / "raw_data"
    matches = sorted(raw_dir.glob("*ΙΑΤΡΙΚΩΝ ΠΡΑΞΕΩΝ*.xls*"))
    if not matches:
        raise FileNotFoundError(f"No medical-act workbook found under {raw_dir}")
    return matches[0]


def derived_lab_cost(section: str, code: str) -> int:
    """The official workbook has no price column; keep a stable load cost by section."""
    numeric = int(re.sub(r"\D", "", code)[-3:] or "0")
    if section == "Γ":
        return 80 + (numeric % 25) * 6
    if section == "Δ":
        return 10 + (numeric % 20) * 3
    return 50 + (numeric % 22) * 5


def extract_lab_tests(source_path: Path, sheet_name: str = "ΤΕΛΙΚΟ") -> list[dict]:
    frame = pd.read_excel(source_path, sheet_name=sheet_name, header=None, dtype=str)
    current_section = ""
    rows: list[dict] = []
    seen_codes: set[str] = set()

    for _, raw_row in frame.iterrows():
        values = [clean(value) for value in raw_row.tolist()]
        non_empty = [value for value in values if value]
        if not non_empty:
            continue

        joined = " | ".join(non_empty)
        heading_match = re.match(r"^([Α-Ω])\.", joined)
        if heading_match:
            current_section = heading_match.group(1)

        if current_section not in SECTION_TO_LAB_TYPE:
            continue

        code = clean(raw_row.iloc[1] if len(raw_row) > 1 else "")
        description = clean(raw_row.iloc[2] if len(raw_row) > 2 else "")
        if not re.fullmatch(r"[A-Z][0-9]{6}", code):
            continue
        if not description or code in seen_codes:
            continue

        seen_codes.add(code)
        rows.append({
            "LabCode": code,
            "LabType": SECTION_TO_LAB_TYPE[current_section],
            "LabDescription": description,
            "LabCost": derived_lab_cost(current_section, code),
            "IsActive": 0 if "ΑΝΕΝΕΡΓΟΣ" in description.upper() else 1,
        })

    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["LabCode", "LabType", "LabDescription", "LabCost", "IsActive"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Extract official lab-test catalog rows from sections Γ, Δ, Ε of the medical-act workbook."
    )
    parser.add_argument("--project-root", default=str(project_root))
    parser.add_argument("--source", default=None, help="Path to the official medical-act .xls/.xlsx workbook.")
    parser.add_argument("--output", default=None, help="Output CSV path. Defaults to data/lab_test.csv.")
    parser.add_argument("--sheet", default="ΤΕΛΙΚΟ")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    source = Path(args.source).expanduser().resolve() if args.source else default_source_path(root)
    output = Path(args.output).expanduser().resolve() if args.output else root / "data" / "lab_test.csv"

    rows = extract_lab_tests(source, args.sheet)
    if not rows:
        raise RuntimeError(f"No Γ/Δ/Ε lab-test rows were extracted from {source}")
    write_csv(output, rows)
    print(f"Wrote {len(rows)} lab tests to {output}")


if __name__ == "__main__":
    main()
