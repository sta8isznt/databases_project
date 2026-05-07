#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd


SECTION_TO_PROC_TYPE = {
    "Α": "Therapeutic",
    "Β": "Surgical",
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


def fit_proc_name(description: str) -> str:
    # ProcedureType.ProcName is varchar(50) in the current schema.
    return description[:50]


def derived_duration(section: str, code: str, description: str) -> int:
    numeric = int(re.sub(r"\D", "", code)[-3:] or "0")
    upper = description.upper()
    if section == "Α":
        return 45 + (numeric % 4) * 15
    if any(token in upper for token in ("ΜΕΓΑΛ", "ΑΝΟΙΚΤ", "ΕΚΤΟΜ", "ΑΦΑΙΡ", "ΜΕΤΑΜΟΣΧ")):
        return 120 + (numeric % 5) * 30
    return 60 + (numeric % 6) * 20


def derived_cost(section: str, code: str, description: str) -> int:
    numeric = int(re.sub(r"\D", "", code)[-4:] or "0")
    upper = description.upper()
    if section == "Α":
        return 120 + (numeric % 20) * 15
    base = 450
    if any(token in upper for token in ("ΜΕΓΑΛ", "ΜΕΤΑΜΟΣΧ", "ΚΑΡΔΙΑ", "ΘΩΡΑΚ")):
        base = 1500
    elif any(token in upper for token in ("ΕΚΤΟΜ", "ΑΦΑΙΡ", "ΑΝΑΣΤΟΜ", "ΑΡΘΡΟΠΛΑΣ")):
        base = 900
    return base + (numeric % 25) * 80


def extract_procedure_types(source_path: Path, sheet_name: str = "ΤΕΛΙΚΟ") -> list[dict]:
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

        if current_section not in SECTION_TO_PROC_TYPE:
            continue

        code = clean(raw_row.iloc[1] if len(raw_row) > 1 else "")
        description = clean(raw_row.iloc[2] if len(raw_row) > 2 else "")
        if not re.fullmatch(r"[A-Z][0-9]{6}", code):
            continue
        if not description or code in seen_codes:
            continue

        seen_codes.add(code)
        rows.append({
            "ProcCode": code,
            "ProcName": fit_proc_name(description),
            "ProcType": SECTION_TO_PROC_TYPE[current_section],
            "ProcDuration": derived_duration(current_section, code, description),
            "ProcCost": derived_cost(current_section, code, description),
        })

    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["ProcCode", "ProcName", "ProcType", "ProcDuration", "ProcCost"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Extract official procedure catalog rows from sections Α and Β of the medical-act workbook."
    )
    parser.add_argument("--project-root", default=str(project_root))
    parser.add_argument("--source", default=None, help="Path to the official medical-act .xls/.xlsx workbook.")
    parser.add_argument("--output", default=None, help="Output CSV path. Defaults to data/procedure_type.csv.")
    parser.add_argument("--sheet", default="ΤΕΛΙΚΟ")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    source = Path(args.source).expanduser().resolve() if args.source else default_source_path(root)
    output = Path(args.output).expanduser().resolve() if args.output else root / "data" / "procedure_type.csv"

    rows = extract_procedure_types(source, args.sheet)
    if not rows:
        raise RuntimeError(f"No Α/Β procedure rows were extracted from {source}")
    write_csv(output, rows)
    print(f"Wrote {len(rows)} procedure types to {output}")


if __name__ == "__main__":
    main()
