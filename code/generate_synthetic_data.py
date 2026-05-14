#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections.abc import Sequence
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


SEED = 20260507
AS_OF_DATE = date(2026, 5, 7)
SHIFT_WEEK_START = date(2026, 3, 9)

# Scale targets for the operational synthetic dataset. Reference catalogs
# (diagnosis, cost, procedure_type, lab_test, and Article 57 drug references)
# are read as fixed inputs and are not regenerated here.
DOCTORS_PER_DEPARTMENT = 20
NURSES_PER_DEPARTMENT = 36
ADMINS_PER_DEPARTMENT = 12
ROOMS_PER_DEPARTMENT = 50
PROCEDURE_ROOM_COUNT = 20

SYNTHETIC_PATIENT_COUNT = 900
SYNTHETIC_HOSPITALIZATION_COUNT = 3600
SYNTHETIC_TRIAGE_COUNT = 4200
SYNTHETIC_ACCEPTED_TRIAGE_COUNT = 2600
SYNTHETIC_EVALUATION_COUNT = 2800
SYNTHETIC_LAB_EVENT_COUNT = 2600
SYNTHETIC_PROCEDURE_EVENT_COUNT = 1200
SYNTHETIC_PRESCRIPTION_COUNT = 3000
SYNTHETIC_ALLERGY_PATIENT_COUNT = 220
SYNTHETIC_PAIRED_PRESCRIPTION_COUNT = 500
SYNTHETIC_STAFF_IMAGE_COUNT = 90
SYNTHETIC_ROOM_IMAGE_COUNT = 90

DEPARTMENT_KEN_POOL_SIZE = 6

DEPARTMENTS = [
    ("Cardiology", "Cardiology", 1, "Building A", ["I21", "I25", "I50", "I48", "I20"]),
    ("Surgery", "Surgery", 2, "Building A", ["K35", "K40", "K80", "T81", "S72"]),
    ("ICU", "IntensiveCare", 3, "Building A", ["J96", "A41", "I46", "R57", "G93"]),
    ("Emergency", "EmergencyMed", 0, "Building B", ["R07", "R10", "S09", "T14", "R55"]),
    ("Neurology", "Neurology", 2, "Building B", ["G40", "G41", "I63", "I64", "G45"]),
    ("Orthopedics", "Orthopedics", 3, "Building B", ["M16", "M17", "S72", "S82", "M25"]),
    ("Pulmonology", "Pulmonology", 4, "Building A", ["J18", "J44", "J45", "J96", "J20"]),
    ("Gastroenterology", "Gastroenterology", 4, "Building B", ["K52", "K80", "K92", "K29", "R10"]),
    ("Oncology", "Oncology", 5, "Building C", ["C34", "C18", "C50", "C71", "C25"]),
    ("Pediatrics", "Pediatrics", 1, "Building C", ["J18", "A09", "R50", "J21", "H66"]),
    ("Ophthalmology", "Ophthalmology", 2, "Building C", ["H25", "H26", "H33", "H40", "H10"]),
    ("ENT", "ENT", 2, "Building C", ["H66", "J34", "J02", "R04", "H81"]),
    ("Nephrology", "Nephrology", 3, "Building C", ["N18", "N17", "N20", "I12", "E11"]),
    ("Psychiatry", "Psychiatry", 4, "Building C", ["F32", "F20", "F41", "F10", "R45"]),
    ("Internal Medicine", "InternalMed", 5, "Building A", ["E11", "I10", "J18", "N39", "K52"]),
]

INSURANCE_PROVIDERS = ["EFKA", "PrivateHealth", "ArmyFund", "Uninsured", "StudentFund"]
NATIONALITIES = ["Greek", "Cypriot", "Albanian", "Bulgarian", "Romanian", "Italian", "German"]
PROFESSIONS = ["Teacher", "Engineer", "Driver", "Retired", "Student", "Farmer", "Clerk", "Lawyer", "Technician"]
ADMIN_ROLES = ["Secretary", "Accountant", "Registrar", "Archivist", "BillingOfficer", "HRClerk", "Scheduler", "RecordsClerk"]
OFFICES = ["FrontDesk", "Billing", "Records", "Scheduling", "HR", "Admissions", "WardDesk", "BackOffice"]

FIRST_NAMES_M = [
    "Giorgos", "Nikos", "Dimitris", "Kostas", "Giannis", "Panagiotis", "Vasilis",
    "Petros", "Spyros", "Andreas", "Marios", "Stavros", "Michalis", "Christos",
]
FIRST_NAMES_F = [
    "Maria", "Eleni", "Katerina", "Sofia", "Georgia", "Panagiota", "Vasiliki",
    "Anastasia", "Dimitra", "Ioanna", "Anna", "Natalia", "Evangelia", "Chrysa",
]
LAST_NAMES = [
    "Papadopoulos", "Nikolaou", "Georgiou", "Dimitriou", "Vasiliou", "Petrou",
    "Ioannou", "Kostopoulos", "Pavlidis", "Konstantinou", "Athanasiou",
    "Theodorou", "Sotiriou", "Lazarou", "Alexiou",
]
FATHER_NAMES = ["Ioannis", "Nikolaos", "Dimitrios", "Konstantinos", "Georgios", "Panagiotis", "Christos"]

SYMPTOMS_BY_LEVEL = {
    1: ["Severe chest pain", "Loss of consciousness", "Major trauma", "Severe respiratory distress"],
    2: ["Stroke symptoms", "High fever with confusion", "Acute abdominal pain", "GI bleeding"],
    3: ["Fracture pain", "Dyspnea", "Severe headache", "Moderate dehydration"],
    4: ["Back pain", "Mild asthma", "Persistent cough", "Vomiting"],
    5: ["Medication issue", "Mild rash", "Chronic dizziness", "Ear pain"],
}

Q14_PREFIXES = ["I21", "J18", "K35", "M16", "G40"]
COMMON_SUBSTANCE_PAIRS = [
    ("Paracetamol", "Ibuprofen"),
    ("Amoxicillin", "Omeprazole"),
    ("Metformin", "Atorvastatin"),
]

def parse_args() -> argparse.Namespace:
    script = Path(__file__).resolve()
    project_root = script.parents[1]
    parser = argparse.ArgumentParser(description="Generate loadable operational synthetic data for sql/install.sql.")
    parser.add_argument("--project-root", default=str(project_root), help="Project root containing data/, code/, generated/.")
    parser.add_argument("--output-dir", default=None, help="Directory where CSV outputs are written. Defaults to <project-root>/data.")
    parser.add_argument("--seed", type=int, default=SEED, help="Deterministic random seed.")
    return parser.parse_args()


def clean(value: str | None, max_len: int | None = None) -> str:
    value = "" if value is None else str(value)
    value = re.sub(r"\s+", " ", value.replace("\ufeff", " ")).strip()
    if max_len is not None:
        value = value[:max_len]
    return value


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: "" if row.get(name) is None else row.get(name) for name in fieldnames})


def choose(seq):
    if not isinstance(seq, Sequence):
        seq = tuple(seq)
    return random.choice(seq)


def random_date_between(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def birth_date_for_age(age: int) -> date:
    year = AS_OF_DATE.year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def short_email(first: str, last: str, index: int, domain: str = "hdb.gr") -> str:
    local = f"{first[0].lower()}{last.lower()}{index}"
    return f"{local[:22]}@{domain}"


def phone(existing: set[str], prefix: str = "69") -> str:
    while True:
        value = prefix + "".join(random.choice("0123456789") for _ in range(8))
        if value not in existing:
            existing.add(value)
            return value


def load_diagnosis(source_path: Path) -> list[dict]:
    rows: list[dict] = []
    with source_path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.reader(handle, delimiter=";"):
            if len(raw) < 2:
                continue
            code = clean(raw[0], 10)
            description = clean(raw[1])
            if code and description:
                rows.append({"ICDCode": code, "Description": description})
    return rows


def load_cost(source_path: Path) -> list[dict]:
    rows: list[dict] = []
    with source_path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.reader(handle, delimiter=";"):
            if len(raw) < 4 or raw[0].lower().startswith("column"):
                continue
            code = clean(raw[0], 5)
            description = clean(raw[1])
            try:
                base_cost = int(float(clean(raw[2]).replace(",", ".")))
                predicted = int(float(clean(raw[3]).replace(",", ".")))
            except ValueError:
                continue
            if code and description and base_cost > 0 and predicted > 0:
                rows.append({
                    "KENCode": code,
                    "Description": description,
                    "BaseCost": base_cost,
                    "PredictedAvgTime": predicted,
                })
    return rows


def load_table_csv(path: Path, expected: list[str]) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Required reference file is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected:
            raise ValueError(f"{path} must have columns {expected}; found {reader.fieldnames}")
        return [dict(row) for row in reader]


def load_lab_tests(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run code/preprocess_lab_tests.py before generating synthetic events."
        )

    rows: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["LabCode", "LabType", "LabDescription", "LabCost", "IsActive"]
        if reader.fieldnames != expected:
            raise ValueError(f"{path} must have columns {expected}; found {reader.fieldnames}")
        for raw in reader:
            lab_code = clean(raw["LabCode"], 20)
            lab_type = clean(raw["LabType"], 10)
            description = clean(raw["LabDescription"])
            try:
                lab_cost = int(raw["LabCost"])
                is_active = int(raw["IsActive"])
            except ValueError as exc:
                raise ValueError(f"Invalid numeric value in {path}: {raw}") from exc
            if not lab_code or not lab_type or not description or lab_cost <= 0 or is_active not in (0, 1):
                raise ValueError(f"Invalid lab-test row in {path}: {raw}")
            rows.append({
                "LabCode": lab_code,
                "LabType": lab_type,
                "LabDescription": description,
                "LabCost": lab_cost,
                "IsActive": is_active,
            })
    if not rows:
        raise ValueError(f"{path} is empty")
    return rows


def load_procedure_types(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run code/preprocess_procedure_types.py before generating synthetic events."
        )

    rows: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["ProcCode", "ProcName", "ProcType", "ProcDuration", "ProcCost"]
        if reader.fieldnames != expected:
            raise ValueError(f"{path} must have columns {expected}; found {reader.fieldnames}")
        for raw in reader:
            proc_code = clean(raw["ProcCode"], 20)
            proc_name = clean(raw["ProcName"], 50)
            proc_type = clean(raw["ProcType"], 20)
            try:
                proc_duration = int(raw["ProcDuration"])
                proc_cost = int(raw["ProcCost"])
            except ValueError as exc:
                raise ValueError(f"Invalid numeric value in {path}: {raw}") from exc
            if (
                not proc_code
                or not proc_name
                or proc_type not in ("Surgical", "Diagnostic", "Therapeutic")
                or proc_duration <= 0
                or proc_cost <= 0
            ):
                raise ValueError(f"Invalid procedure-type row in {path}: {raw}")
            rows.append({
                "ProcCode": proc_code,
                "ProcName": proc_name,
                "ProcType": proc_type,
                "ProcDuration": proc_duration,
                "ProcCost": proc_cost,
            })
    if not rows:
        raise ValueError(f"{path} is empty")
    return rows


def build_reference_tables(project_root: Path, output_dir: Path) -> dict:
    diagnosis_source = project_root / "data" / "icd_codes.csv"
    if diagnosis_source.exists():
        diagnosis = load_diagnosis(diagnosis_source)
    else:
        diagnosis = load_table_csv(output_dir / "diagnosis.csv", ["ICDCode", "Description"])

    cost_source = project_root / "data" / "cost_ken_codes_new.csv"
    if not cost_source.exists():
        fallback_cost_source = project_root / "data" / "cost_ken_codes.csv"
        cost_source = fallback_cost_source if fallback_cost_source.exists() else cost_source
    if cost_source.exists():
        cost = load_cost(cost_source)
    else:
        cost = load_table_csv(output_dir / "cost.csv", ["KENCode", "Description", "BaseCost", "PredictedAvgTime"])
    lab_tests = load_lab_tests(output_dir / "lab_test.csv")
    procedure_types = load_procedure_types(output_dir / "procedure_type.csv")

    return {
        "diagnosis": diagnosis,
        "cost": cost,
        "procedure_type": procedure_types,
        "lab_test": lab_tests,
    }


def build_drug_tables(project_root: Path, output_dir: Path) -> dict:
    drug_path = output_dir / "drug_type.csv"
    phone_path = output_dir / "drug_support_phone.csv"
    substance_path = output_dir / "substances.csv"
    has_substance_path = output_dir / "has_substances.csv"

    drug_type_rows = load_table_csv(drug_path, ["DrugID", "Name", "Route", "AuthCountry", "AuthHolder", "MasterFileLocation", "Email"])
    substance_rows = load_table_csv(substance_path, ["ID", "Name"])
    has_substance_rows = load_table_csv(has_substance_path, ["SubID", "DrugID"])
    support_rows = load_table_csv(phone_path, ["DrugID", "Phone"])

    drug_ids = {row["DrugID"] for row in drug_type_rows}

    for row in drug_type_rows:
        if not re.fullmatch(r"[0-9]+", clean(row["DrugID"])):
            raise ValueError(f"Invalid DrugID in {drug_path}: {row}")
        row["DrugID"] = int(row["DrugID"])

    for row in substance_rows:
        if not re.fullmatch(r"[0-9]+", clean(row["ID"])):
            raise ValueError(f"Invalid substance ID in {substance_path}: {row}")
        if not clean(row["Name"]):
            raise ValueError(f"Invalid substance row in {substance_path}: {row}")
        row["ID"] = int(row["ID"])

    drug_ids_int = {row["DrugID"] for row in drug_type_rows}
    substance_ids_int = {row["ID"] for row in substance_rows}
    for row in has_substance_rows:
        drug_id = int(row["DrugID"])
        sub_id = int(row["SubID"])
        if drug_id not in drug_ids_int or sub_id not in substance_ids_int:
            raise ValueError(f"Invalid drug-substance row in {has_substance_path}: {row}")
        row["DrugID"] = drug_id
        row["SubID"] = sub_id

    for row in support_rows:
        drug_id = int(row["DrugID"])
        drug_phone = clean(row["Phone"])
        if str(drug_id) not in drug_ids or not re.fullmatch(r"[0-9]{10,14}", drug_phone):
            raise ValueError(f"Invalid drug support phone row in {phone_path}: {row}")
        row["DrugID"] = drug_id
        row["Phone"] = drug_phone

    return {
        "drug_type": drug_type_rows,
        "drug_support_phone": support_rows,
        "substances": substance_rows,
        "has_substances": has_substance_rows,
    }


def build_staff_and_departments(output_dir: Path) -> dict:
    staff_rows: list[dict] = []
    staff_phone_rows: list[dict] = []
    doctor_rows: list[dict] = []
    department_rows: list[dict] = []
    doctor_department_rows: list[dict] = []
    nurse_rows: list[dict] = []
    admin_rows: list[dict] = []
    room_rows: list[dict] = []
    used_phones: set[str] = set()
    staff_counter = 10000000000
    person_index = 1
    doctors_by_department: dict[int, list[dict]] = {}
    nurses_by_department: dict[int, list[str]] = {}
    admins_by_department: dict[int, list[str]] = {}
    staff_birthdates: dict[str, date] = {}

    doctor_group_ranks = [
        "Director", "Consultant", "Resident",
        "Consultant", "Registrar", "Resident",
        "Consultant", "Registrar", "Resident",
        "Consultant", "Registrar", "Resident",
        "Consultant", "Registrar", "Consultant", "Resident",
        "Consultant", "Registrar", "Consultant", "Resident",
    ][:DOCTORS_PER_DEPARTMENT]

    for dept_id, (dept_name, specialty, floor, building, _) in enumerate(DEPARTMENTS, start=1):
        local_doctors = []
        director_amk = None
        senior_supervisors: list[str] = []
        for local_idx, rank in enumerate(doctor_group_ranks):
            gender = choose(["M", "F"])
            first = choose(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
            last = choose(LAST_NAMES)
            amk = f"{staff_counter:011d}"
            staff_counter += 1
            if rank == "Director":
                age = random.randint(52, 64)
            elif rank == "Consultant":
                age = random.randint(39, 55)
            elif rank == "Registrar":
                age = random.randint(34, 48)
            else:
                age = random.randint(28, 34)
            birth = birth_date_for_age(age)
            hire_start = max(date(birth.year + 25, 1, 1), date(2009, 1, 1))
            hire_date = random_date_between(hire_start, date(2025, 9, 30))
            staff_rows.append({
                "AMKA": amk,
                "FirstName": first,
                "LastName": last,
                "BirthDate": birth.isoformat(),
                "Email": short_email(first, last, person_index),
                "HireDate": hire_date.isoformat(),
                "IsActive": 1,
                "Type": "Doctor",
            })
            staff_phone_rows.append({"StaffAMKA": amk, "Phone": phone(used_phones)})
            staff_birthdates[amk] = birth
            if rank == "Director":
                director_amk = amk
            else:
                senior_supervisors.append(amk)
            local_doctors.append({"AMKA": amk, "Rank": rank, "local_idx": local_idx, "Specialty": specialty})
            person_index += 1

        assert director_amk is not None
        doctors_by_department[dept_id] = local_doctors
        department_rows.append({
            "DepartmentID": dept_id,
            "Name": dept_name,
            "Description": f"{dept_name} department of Ygeiopolis General Hospital",
            "Floor": floor,
            "Building": building,
            "DirectorAMKA": director_amk,
        })

        for doctor in local_doctors:
            if doctor["Rank"] == "Director":
                supervisor = ""
            elif doctor["Rank"] == "Resident":
                supervisor = choose([d["AMKA"] for d in local_doctors if d["Rank"] in ("Consultant", "Registrar")])
            else:
                supervisor = director_amk
            doctor_rows.append({
                "AMKA": doctor["AMKA"],
                "License": f"LIC{dept_id:02d}{doctor['local_idx']:02d}{doctor['AMKA'][-4:]}",
                "Specialty": specialty,
                "Rank": doctor["Rank"],
                "SupervisorAMKA": supervisor,
            })
            doctor_department_rows.append({"DoctorAMKA": doctor["AMKA"], "DepartmentID": dept_id})

    # A few cross-department doctor memberships for M:N coverage.
    for dept_id, doctors in doctors_by_department.items():
        for doctor in doctors:
            if doctor["Rank"] in ("Consultant", "Registrar") and random.random() < 0.12:
                other_dept = random.choice([i for i in range(1, len(DEPARTMENTS) + 1) if i != dept_id])
                doctor_department_rows.append({"DoctorAMKA": doctor["AMKA"], "DepartmentID": other_dept})

    for dept_id in range(1, len(DEPARTMENTS) + 1):
        nurses = []
        for idx in range(NURSES_PER_DEPARTMENT):
            gender = choose(["M", "F"])
            first = choose(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
            last = choose(LAST_NAMES)
            amk = f"{staff_counter:011d}"
            staff_counter += 1
            rank = "HeadNurse" if idx == 0 else ("AssistantNurse" if idx < max(7, NURSES_PER_DEPARTMENT // 4) else "Nurse")
            age = random.randint(42, 58) if rank == "HeadNurse" else random.randint(24, 50)
            birth = birth_date_for_age(age)
            hire_date = random_date_between(max(date(birth.year + 21, 1, 1), date(2012, 1, 1)), date(2025, 9, 30))
            staff_rows.append({
                "AMKA": amk,
                "FirstName": first,
                "LastName": last,
                "BirthDate": birth.isoformat(),
                "Email": short_email(first, last, person_index),
                "HireDate": hire_date.isoformat(),
                "IsActive": 1,
                "Type": "Nurse",
            })
            staff_phone_rows.append({"StaffAMKA": amk, "Phone": phone(used_phones)})
            staff_birthdates[amk] = birth
            nurse_rows.append({"AMKA": amk, "Rank": rank, "DepartmentID": dept_id})
            nurses.append(amk)
            person_index += 1
        nurses_by_department[dept_id] = nurses

    for dept_id in range(1, len(DEPARTMENTS) + 1):
        admins = []
        for idx in range(ADMINS_PER_DEPARTMENT):
            gender = choose(["M", "F"])
            first = choose(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
            last = choose(LAST_NAMES)
            amk = f"{staff_counter:011d}"
            staff_counter += 1
            age = random.randint(24, 58)
            birth = birth_date_for_age(age)
            hire_date = random_date_between(max(date(birth.year + 21, 1, 1), date(2013, 1, 1)), date(2025, 9, 30))
            staff_rows.append({
                "AMKA": amk,
                "FirstName": first,
                "LastName": last,
                "BirthDate": birth.isoformat(),
                "Email": short_email(first, last, person_index),
                "HireDate": hire_date.isoformat(),
                "IsActive": 1,
                "Type": "AdminStaff",
            })
            staff_phone_rows.append({"StaffAMKA": amk, "Phone": phone(used_phones)})
            staff_birthdates[amk] = birth
            admin_rows.append({
                "AMKA": amk,
                "Role": ADMIN_ROLES[idx % len(ADMIN_ROLES)],
                "Office": OFFICES[idx % len(OFFICES)],
                "DepartmentID": dept_id,
            })
            admins.append(amk)
            person_index += 1
        admins_by_department[dept_id] = admins

    for dept_id, (dept_name, _, _, _, _) in enumerate(DEPARTMENTS, start=1):
        for room_id in range(1, ROOMS_PER_DEPARTMENT + 1):
            room_type = "ICU" if dept_name == "ICU" or room_id <= 2 else ("Single" if room_id % 5 == 0 else "MultiBed")
            room_rows.append({
                "ID": room_id,
                "DepartmentID": dept_id,
                "Type": room_type,
                "State": "Available",
            })

    write_csv(output_dir / "staff.csv", ["AMKA", "FirstName", "LastName", "BirthDate", "Email", "HireDate", "IsActive", "Type"], staff_rows)
    write_csv(output_dir / "staff_phone.csv", ["StaffAMKA", "Phone"], staff_phone_rows)
    write_csv(output_dir / "doctor.csv", ["AMKA", "License", "Specialty", "Rank", "SupervisorAMKA"], doctor_rows)
    write_csv(output_dir / "department.csv", ["DepartmentID", "Name", "Description", "Floor", "Building", "DirectorAMKA"], department_rows)
    write_csv(output_dir / "doctor_department.csv", ["DoctorAMKA", "DepartmentID"], sorted(doctor_department_rows, key=lambda r: (r["DepartmentID"], r["DoctorAMKA"])))
    write_csv(output_dir / "nurse.csv", ["AMKA", "Rank", "DepartmentID"], nurse_rows)
    write_csv(output_dir / "admin_staff.csv", ["AMKA", "Role", "Office", "DepartmentID"], admin_rows)
    write_csv(output_dir / "room.csv", ["ID", "DepartmentID", "Type", "State"], room_rows)

    return {
        "staff": staff_rows,
        "staff_phone": staff_phone_rows,
        "doctor": doctor_rows,
        "department": department_rows,
        "doctor_department": doctor_department_rows,
        "nurse": nurse_rows,
        "admin_staff": admin_rows,
        "room": room_rows,
        "doctors_by_department": doctors_by_department,
        "nurses_by_department": nurses_by_department,
        "admins_by_department": admins_by_department,
        "staff_birthdates": staff_birthdates,
    }


def build_patients(output_dir: Path, count: int = SYNTHETIC_PATIENT_COUNT) -> dict:
    used_phones: set[str] = set()
    patient_rows = []
    patient_phone_rows = []
    contact_rows = []
    contact_phone_rows = []
    patient_counter = 30000000000
    contact_id = 1

    insurance_rows = [{"Name": name} for name in INSURANCE_PROVIDERS]

    for idx in range(1, count + 1):
        gender = choose(["M", "F"])
        first = choose(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
        last = choose(LAST_NAMES)
        amka = f"{patient_counter:011d}"
        patient_counter += 1
        age = random.randint(1, 92)
        patient_rows.append({
            "AMKA": amka,
            "FirstName": first,
            "LastName": last,
            "FatherName": choose(FATHER_NAMES),
            "BirthDate": birth_date_for_age(age).isoformat(),
            "Gender": gender,
            "Weight": round(random.uniform(9.0, 120.0), 1) if age > 1 else round(random.uniform(3.0, 12.0), 1),
            "Height": round(random.uniform(70.0, 195.0), 1),
            "Address": f"{choose(['Athens', 'Piraeus', 'Patras', 'Larisa', 'Volos'])} {random.randint(1, 150)}",
            "Email": short_email(first, last, idx, "mail.gr"),
            "Profession": choose(PROFESSIONS),
            "Nationality": choose(NATIONALITIES),
            "isActive": 1,
            "InsuranceProviderName": random.choices(INSURANCE_PROVIDERS, weights=[55, 15, 10, 10, 10])[0],
        })
        patient_phone_rows.append({"PatientAMKA": amka, "Phone": phone(used_phones)})

        for _ in range(1 + (1 if random.random() < 0.25 else 0)):
            cf = choose(FIRST_NAMES_M + FIRST_NAMES_F)
            cl = choose(LAST_NAMES)
            contact_rows.append({
                "ID": contact_id,
                "PatientAMKA": amka,
                "FirstName": cf,
                "LastName": cl,
                "Address": f"{choose(['Athens', 'Piraeus', 'Patras'])} {random.randint(1, 150)}",
                "Email": short_email(cf, cl, contact_id, "cnt.gr"),
                "Relation": choose(["Spouse", "Parent", "Sibling", "Child", "Friend"]),
            })
            contact_phone_rows.append({"ID": contact_id, "Phone": phone(used_phones, "21")})
            contact_id += 1

    write_csv(output_dir / "insurance_provider.csv", ["Name"], insurance_rows)
    write_csv(output_dir / "patient.csv", [
        "AMKA", "FirstName", "LastName", "FatherName", "BirthDate", "Gender", "Weight", "Height",
        "Address", "Email", "Profession", "Nationality", "isActive", "InsuranceProviderName",
    ], patient_rows)
    write_csv(output_dir / "patient_phone.csv", ["PatientAMKA", "Phone"], patient_phone_rows)
    write_csv(output_dir / "emergency_contact.csv", ["ID", "PatientAMKA", "FirstName", "LastName", "Address", "Email", "Relation"], contact_rows)
    write_csv(output_dir / "em_contact_phone.csv", ["ID", "Phone"], contact_phone_rows)

    return {
        "insurance_provider": insurance_rows,
        "patient": patient_rows,
        "patient_phone": patient_phone_rows,
        "emergency_contact": contact_rows,
        "em_contact_phone": contact_phone_rows,
    }


def build_shifts(output_dir: Path, org: dict) -> dict:
    shift_types = [
        {"Name": "Morning", "StartTime": "07:00:00"},
        {"Name": "Afternoon", "StartTime": "15:00:00"},
        {"Name": "Night", "StartTime": "23:00:00"},
    ]
    shift_rows = []
    has_doctor_rows = []
    has_nurse_rows = []
    has_admin_rows = []

    for dept_id in range(1, len(DEPARTMENTS) + 1):
        doctors = org["doctors_by_department"][dept_id]
        doctor_groups = {
            "Morning": doctors[0:3],
            "Afternoon": doctors[3:6],
            "NightA": doctors[6:9],
            "NightB": doctors[9:12],
        }
        nurses = org["nurses_by_department"][dept_id]
        nurse_groups = {
            "Morning": nurses[0:6],
            "Afternoon": nurses[6:12],
            "NightA": nurses[12:18],
            "NightB": nurses[18:24],
        }
        admins = org["admins_by_department"][dept_id]
        admin_groups = {
            "Morning": admins[0:2],
            "Afternoon": admins[2:4],
            "NightA": admins[4:6],
            "NightB": admins[6:8],
        }

        for day_idx in range(7):
            shift_date = SHIFT_WEEK_START + timedelta(days=day_idx)
            for shift_name in ["Morning", "Afternoon", "Night"]:
                shift_rows.append({"DepartmentID": dept_id, "ShiftTypeName": shift_name, "Date": shift_date.isoformat()})
                group_key = shift_name
                if shift_name == "Night":
                    group_key = "NightA" if day_idx in (0, 1, 2, 6) else "NightB"

                # Senior rows are deliberately before residents because the trigger checks resident inserts.
                group_doctors = sorted(doctor_groups[group_key], key=lambda d: d["Rank"] == "Resident")
                for doctor in group_doctors:
                    has_doctor_rows.append({
                        "DepartmentID": dept_id,
                        "ShiftTypeName": shift_name,
                        "ShiftDate": shift_date.isoformat(),
                        "DoctorAMKA": doctor["AMKA"],
                    })
                for nurse_amk in nurse_groups[group_key]:
                    has_nurse_rows.append({
                        "DepartmentID": dept_id,
                        "ShiftTypeName": shift_name,
                        "ShiftDate": shift_date.isoformat(),
                        "NurseAMKA": nurse_amk,
                    })
                for admin_amk in admin_groups[group_key]:
                    has_admin_rows.append({
                        "DepartmentID": dept_id,
                        "ShiftTypeName": shift_name,
                        "ShiftDate": shift_date.isoformat(),
                        "AdminAMKA": admin_amk,
                    })

    write_csv(output_dir / "shift_type.csv", ["Name", "StartTime"], shift_types)
    write_csv(output_dir / "shift.csv", ["DepartmentID", "ShiftTypeName", "Date"], shift_rows)
    write_csv(output_dir / "has_doctor.csv", ["DepartmentID", "ShiftTypeName", "ShiftDate", "DoctorAMKA"], has_doctor_rows)
    write_csv(output_dir / "has_nurse.csv", ["DepartmentID", "ShiftTypeName", "ShiftDate", "NurseAMKA"], has_nurse_rows)
    write_csv(output_dir / "has_admin.csv", ["DepartmentID", "ShiftTypeName", "ShiftDate", "AdminAMKA"], has_admin_rows)
    return {
        "shift_type": shift_types,
        "shift": shift_rows,
        "has_doctor": has_doctor_rows,
        "has_nurse": has_nurse_rows,
        "has_admin": has_admin_rows,
    }


def build_icd_index(diagnosis_rows: list[dict]) -> dict[str, list[str]]:
    by_prefix: dict[str, list[str]] = defaultdict(list)
    for row in diagnosis_rows:
        code = row["ICDCode"]
        match = re.match(r"^([A-Z][0-9]{2})", code)
        if match:
            by_prefix[match.group(1)].append(code)
    return by_prefix


def build_hospitalizations(output_dir: Path, ref: dict, org: dict, patients: dict) -> dict:
    by_prefix = build_icd_index(ref["diagnosis"])
    available_prefixes = sorted(by_prefix)
    cost_rows = ref["cost"]
    patient_ids = [row["AMKA"] for row in patients["patient"]]
    patients_by_insurance: dict[str, list[str]] = defaultdict(list)
    for row in patients["patient"]:
        patients_by_insurance[row["InsuranceProviderName"]].append(row["AMKA"])
    room_count_by_dept = defaultdict(int)
    for row in org["room"]:
        room_count_by_dept[row["DepartmentID"]] += 1
    department_ken_pools: dict[int, list[dict]] = {
        dept_id: random.sample(cost_rows, min(DEPARTMENT_KEN_POOL_SIZE, len(cost_rows)))
        for dept_id in range(1, len(DEPARTMENTS) + 1)
    }

    hospitalizations = []
    admission_diag = []
    exit_diag = []
    used_patient_admissions: set[tuple[str, str]] = set()
    hosp_id = 1
    meta: dict[int, dict] = {}

    def pick_prefix(dept_id: int, forced: str | None = None) -> str:
        if forced and forced in by_prefix:
            return forced
        prefs = [p for p in DEPARTMENTS[dept_id - 1][4] if p in by_prefix and p not in Q14_PREFIXES]
        if prefs:
            return choose(prefs)
        non_q14 = [p for p in available_prefixes if p not in Q14_PREFIXES]
        return choose(non_q14 or available_prefixes)

    def choose_ken(dept_id: int) -> dict:
        pool = department_ken_pools[dept_id]
        weights = [9 if idx < 2 else 4 if idx < 4 else 2 for idx, _ in enumerate(pool)]
        return random.choices(pool, weights=weights, k=1)[0]

    def choose_patient_for_insurance(insurance_name: str) -> str:
        return choose(patients_by_insurance.get(insurance_name) or patient_ids)

    def generated_stay_days(predicted_days: int) -> int:
        if random.random() < 0.45:
            return predicted_days + random.randint(1, max(2, min(8, predicted_days + 2)))
        reduction = random.randint(0, max(0, min(3, predicted_days - 1)))
        return max(1, predicted_days - reduction + random.randint(0, 2))

    def add_hospitalization(patient_amka: str, dept_id: int, admission: datetime, stay_days: int | None = None, forced_prefix: str | None = None) -> None:
        nonlocal hosp_id
        admission_key = admission.strftime("%Y-%m-%d %H:%M:%S")
        while (patient_amka, admission_key) in used_patient_admissions:
            admission += timedelta(hours=1)
            admission_key = admission.strftime("%Y-%m-%d %H:%M:%S")
        used_patient_admissions.add((patient_amka, admission_key))

        prefix = pick_prefix(dept_id, forced_prefix)
        adm_code = choose(by_prefix[prefix])
        out_code = adm_code if random.random() < 0.65 else choose(by_prefix[prefix])
        ken = choose_ken(dept_id)
        predicted = int(ken["PredictedAvgTime"])
        if stay_days is None or stay_days <= 0:
            stay_days = generated_stay_days(predicted)
        exit_dt = admission + timedelta(days=stay_days, hours=random.randint(2, 10))
        room_id = ((hosp_id + dept_id) % room_count_by_dept[dept_id]) + 1
        hospitalizations.append({
            "HospitalizationID": hosp_id,
            "AdmissionDateTime": admission.strftime("%Y-%m-%d %H:%M:%S"),
            "PatientAMKA": patient_amka,
            "ExitDateTime": exit_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "RoomID": room_id,
            "DepartmentID": dept_id,
            "KENcode": ken["KENCode"],
        })
        admission_diag.append({"HospitalizationID": hosp_id, "ICDCode": adm_code})
        exit_diag.append({"HospitalizationID": hosp_id, "ICDCode": out_code})
        meta[hosp_id] = {
            "patient": patient_amka,
            "department": dept_id,
            "admission": admission,
            "exit": exit_dt,
            "ken": ken["KENCode"],
            "admission_icd": adm_code,
            "exit_icd": out_code,
        }
        hosp_id += 1

    # Q3: repeated hospitalizations in the same department.
    for patient_amka in patient_ids[:12]:
        dept_id = random.randint(1, len(DEPARTMENTS))
        base = datetime(2025, random.randint(1, 4), random.randint(1, 20), 9, 0, 0)
        for offset in range(4):
            add_hospitalization(patient_amka, dept_id, base + timedelta(days=65 * offset), random.randint(2, 7))

    # Q9: paired patients with equal total hospitalization days in 2026 and total > 15.
    pair_source = patient_ids[20:40]
    for idx in range(0, 10, 2):
        total_parts = [5, 6, 7]
        for patient_amka in (pair_source[idx], pair_source[idx + 1]):
            base = datetime(2026, 1 + idx, 5, 10, 0, 0)
            for part_idx, days in enumerate(total_parts):
                add_hospitalization(patient_amka, random.randint(1, len(DEPARTMENTS)), base + timedelta(days=45 * part_idx), days)

    # Q14: equal admission counts for selected ICD-10 categories in two consecutive years.
    for prefix in [p for p in Q14_PREFIXES if p in by_prefix]:
        for year in (2025, 2026):
            for seq in range(6):
                add_hospitalization(
                    choose(patient_ids),
                    random.randint(1, len(DEPARTMENTS)),
                    datetime(year, 2 + seq, 10 + seq, 11, 0, 0),
                    random.randint(2, 6),
                    forced_prefix=prefix,
                )

    filler_seq = 0
    while len(hospitalizations) < SYNTHETIC_HOSPITALIZATION_COUNT:
        dept_id = (filler_seq % len(DEPARTMENTS)) + 1
        year = 2025 + ((filler_seq // len(DEPARTMENTS)) % 2)
        month = ((filler_seq // (len(DEPARTMENTS) * 2)) % 12) + 1
        day = (filler_seq % 24) + 1
        hour = 7 + (filler_seq % 12)
        insurance_name = INSURANCE_PROVIDERS[(filler_seq // (len(DEPARTMENTS) * 2 * 3)) % len(INSURANCE_PROVIDERS)]
        admission = datetime(year, month, day, hour, 0, 0)
        add_hospitalization(choose_patient_for_insurance(insurance_name), dept_id, admission)
        filler_seq += 1

    write_csv(output_dir / "hospitalization.csv", [
        "HospitalizationID", "AdmissionDateTime", "PatientAMKA", "ExitDateTime", "RoomID", "DepartmentID", "KENcode",
    ], hospitalizations)
    write_csv(output_dir / "admission_diagnosis.csv", ["HospitalizationID", "ICDCode"], admission_diag)
    write_csv(output_dir / "exit_diagnosis.csv", ["HospitalizationID", "ICDCode"], exit_diag)
    return {
        "hospitalization": hospitalizations,
        "admission_diagnosis": admission_diag,
        "exit_diagnosis": exit_diag,
        "hospitalization_meta": meta,
    }


def doctor_pool_by_dept(org: dict) -> dict[int, list[str]]:
    return {
        dept_id: [doctor["AMKA"] for doctor in doctors]
        for dept_id, doctors in org["doctors_by_department"].items()
    }


def build_triage_events(output_dir: Path, org: dict, patients: dict, clinical: dict) -> dict:
    emergency_dept_id = next(idx for idx, row in enumerate(DEPARTMENTS, start=1) if row[0] == "Emergency")
    triage_nurses = org["nurses_by_department"][emergency_dept_id]
    patient_ids = [row["AMKA"] for row in patients["patient"]]
    triage_rows = []
    used_triage_times: set[tuple[str, str]] = set()
    triage_id = 1

    def add_triage(patient_amka: str, triage_dt: datetime, level: int, outcome: str, hosp_id: int | str, admission_dt: datetime | None = None) -> None:
        nonlocal triage_id
        key = (patient_amka, triage_dt.strftime("%Y-%m-%d %H:%M:%S"))
        while key in used_triage_times:
            triage_dt += timedelta(minutes=1)
            key = (patient_amka, triage_dt.strftime("%Y-%m-%d %H:%M:%S"))
        used_triage_times.add(key)
        
        # Generate AssesmentDateTime
        if outcome == "Accepted" and admission_dt is not None:
            # For accepted triages: AssesmentDateTime should be between TriageDateTime and AdmissionDateTime
            # Typically assessment happens 30 minutes to 2 hours after triage
            time_gap_minutes = random.randint(30, 120)
            assesment_dt = triage_dt + timedelta(minutes=time_gap_minutes)
            # Ensure it doesn't exceed admission time
            if assesment_dt > admission_dt:
                assesment_dt = admission_dt - timedelta(minutes=random.randint(5, 30))
        else:
            # For discarded triages: AssesmentDateTime should be after TriageDateTime (30 min to 4 hours)
            time_gap_minutes = random.randint(30, 240)
            assesment_dt = triage_dt + timedelta(minutes=time_gap_minutes)
        
        assesment_str = assesment_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        triage_rows.append({
            "TriageID": triage_id,
            "Symptoms": choose(SYMPTOMS_BY_LEVEL[level]),
            "EmergencyLevel": level,
            "Outcome": outcome,
            "TriageDateTime": key[1],
            "HospitalizationID": hosp_id,
            "AssesmentDateTime": assesment_str,
            "PatientAMKA": patient_amka,
            "NurseAMKA": choose(triage_nurses),
        })
        triage_id += 1

    accepted_count = min(SYNTHETIC_ACCEPTED_TRIAGE_COUNT, len(clinical["hospitalization"]))
    for hosp in clinical["hospitalization"][:accepted_count]:
        level = random.choices([1, 2, 3, 4, 5], weights=[8, 20, 35, 25, 12])[0]
        admission = clinical["hospitalization_meta"][hosp["HospitalizationID"]]["admission"]
        triage_time = admission - timedelta(hours=random.randint(1, 7))
        add_triage(hosp["PatientAMKA"], triage_time, level, "Accepted", hosp["HospitalizationID"], admission)

    while len(triage_rows) < SYNTHETIC_TRIAGE_COUNT:
        level = random.choices([1, 2, 3, 4, 5], weights=[5, 15, 30, 32, 18])[0]
        arrival = datetime(2025, 1, 1, 8, 0, 0) + timedelta(days=random.randint(0, 720), minutes=random.randint(0, 1439))
        add_triage(choose(patient_ids), arrival, level, "Discarded", "")

    write_csv(output_dir / "triage_event.csv", [
        "TriageID", "Symptoms", "EmergencyLevel", "Outcome", "TriageDateTime", "HospitalizationID", "PatientAMKA", "AssesmentDateTime", "NurseAMKA",
    ], triage_rows)
    return {"triage_event": triage_rows}


def build_evaluations(output_dir: Path, clinical: dict, prescriptions: dict) -> dict:
    doctors_by_hospitalization: dict[int, set[str]] = defaultdict(set)
    for row in prescriptions["prescription_event"]:
        doctors_by_hospitalization[int(row["HospitalizationID"])].add(row["DoctorAMKA"])

    candidate_ids = [
        row["HospitalizationID"]
        for row in clinical["hospitalization"]
        if row["HospitalizationID"] in doctors_by_hospitalization
    ]
    if not candidate_ids:
        raise RuntimeError("Cannot generate DoctorEvaluation rows without prescription events.")

    selected_ids = random.sample(candidate_ids, min(SYNTHETIC_EVALUATION_COUNT, len(candidate_ids)))
    hosp_eval_rows = []
    doctor_eval_rows = []
    for hospitalization_id in selected_ids:
        hosp_eval_rows.append({
            "HospitalizationID": hospitalization_id,
            "QoNurseS": random.choices([2, 3, 4, 5], weights=[4, 16, 38, 42])[0],
            "Cleanliness": random.choices([2, 3, 4, 5], weights=[6, 20, 36, 38])[0],
            "Food": random.choices([1, 2, 3, 4, 5], weights=[5, 12, 25, 35, 23])[0],
            "GeneralExperience": random.choices([2, 3, 4, 5], weights=[5, 15, 40, 40])[0],
        })
        for doctor_amka in sorted(doctors_by_hospitalization[hospitalization_id]):
            doctor_eval_rows.append({
                "HospitalizationID": hospitalization_id,
                "DoctorAMKA": doctor_amka,
                "QoDoctorS": random.choices([2, 3, 4, 5], weights=[5, 15, 40, 40])[0],
            })

    write_csv(output_dir / "hosp_evaluation.csv", [
        "HospitalizationID", "QoNurseS", "Cleanliness", "Food", "GeneralExperience",
    ], hosp_eval_rows)
    write_csv(output_dir / "doctor_evaluation.csv", [
        "HospitalizationID", "DoctorAMKA", "QoDoctorS",
    ], doctor_eval_rows)

    legacy_path = output_dir / "evaluation.csv"
    if legacy_path.exists():
        legacy_path.unlink()

    return {"hosp_evaluation": hosp_eval_rows, "doctor_evaluation": doctor_eval_rows}


def build_labs(output_dir: Path, ref: dict, org: dict, clinical: dict) -> dict:
    doctor_by_dept = doctor_pool_by_dept(org)
    lab_codes = [row["LabCode"] for row in ref["lab_test"]]
    lab_rows = []
    used_lab_events: set[tuple[int, str, str]] = set()
    lab_id = 1
    attempts = 0
    max_attempts = SYNTHETIC_LAB_EVENT_COUNT * 30
    while len(lab_rows) < SYNTHETIC_LAB_EVENT_COUNT and attempts < max_attempts:
        attempts += 1
        hosp = choose(clinical["hospitalization"])
        info = clinical["hospitalization_meta"][hosp["HospitalizationID"]]
        hours_span = max(8, int((info["exit"] - info["admission"]).total_seconds() // 3600) - 4)
        lab_dt = info["admission"] + timedelta(hours=random.randint(3, hours_span))
        lab_dt_text = lab_dt.strftime("%Y-%m-%d %H:%M:%S")
        lab_code = choose(lab_codes)
        key = (hosp["HospitalizationID"], lab_code, lab_dt_text)
        if key in used_lab_events:
            continue
        used_lab_events.add(key)
        lab_rows.append({
            "Id": lab_id,
            "HospitalizationID": hosp["HospitalizationID"],
            "LabCode": lab_code,
            "LabDateTime": lab_dt_text,
            "LabResult": choose(["Normal", "Mildly abnormal", "Follow up required", "Improved", "Critical value reviewed"]),
            "PendingResult": 0,
            "DoctorAMKA": choose(doctor_by_dept[info["department"]]),
        })
        lab_id += 1

    write_csv(output_dir / "hosp_lab_test.csv", [
        "Id", "HospitalizationID", "LabCode", "LabDateTime", "LabResult", "PendingResult", "DoctorAMKA",
    ], lab_rows)
    return {"hosp_lab_test": lab_rows}


def procedure_room_rows() -> list[dict]:
    rows = []
    operating_room_limit = max(1, int(PROCEDURE_ROOM_COUNT * 0.7))
    for room_id in range(1, PROCEDURE_ROOM_COUNT + 1):
        rows.append({
            "ProcRoomID": room_id,
            "ProcRoomType": "OperatingRoom" if room_id <= operating_room_limit else "InterventionRoom",
            "State": "Available",
        })
    return rows


def overlaps(schedule: list[tuple[datetime, datetime]], start: datetime, end: datetime) -> bool:
    return any(start < old_end and old_start < end for old_start, old_end in schedule)


def build_procedures(output_dir: Path, ref: dict, org: dict, clinical: dict) -> dict:
    proc_rooms = procedure_room_rows()
    proc_by_code = {row["ProcCode"]: row for row in ref["procedure_type"]}
    surgical_codes = [row["ProcCode"] for row in ref["procedure_type"] if row["ProcType"] == "Surgical"]
    other_codes = [row["ProcCode"] for row in ref["procedure_type"] if row["ProcType"] != "Surgical"]
    doctor_by_dept = doctor_pool_by_dept(org)
    young_doctors = [
        row["AMKA"] for row in org["doctor"]
        if (AS_OF_DATE.year - org["staff_birthdates"][row["AMKA"]].year) < 35
    ]

    procedure_rows = []
    operates_rows = []
    assists_rows = []
    helps_rows = []
    room_schedule: dict[int, list[tuple[datetime, datetime]]] = defaultdict(list)
    doctor_schedule: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    proc_event_id = 1

    candidates = [h for h in clinical["hospitalization"] if h["AdmissionDateTime"].startswith("2026")]
    if len(candidates) < SYNTHETIC_PROCEDURE_EVENT_COUNT:
        candidates = clinical["hospitalization"]
    random.shuffle(candidates)

    for hosp in candidates:
        if len(procedure_rows) >= SYNTHETIC_PROCEDURE_EVENT_COUNT:
            break
        info = clinical["hospitalization_meta"][hosp["HospitalizationID"]]
        code = choose(surgical_codes if random.random() < 0.78 else other_codes)
        proc = proc_by_code[code]
        duration = int(proc["ProcDuration"])
        room_candidates = [r["ProcRoomID"] for r in proc_rooms if (proc["ProcType"] == "Surgical") == (r["ProcRoomType"] == "OperatingRoom")]
        if not room_candidates:
            room_candidates = [r["ProcRoomID"] for r in proc_rooms]

        dept_doctors = doctor_by_dept[info["department"]]
        main_pool = dept_doctors[:]
        if proc_event_id % 8 == 0 and young_doctors:
            main_pool = young_doctors

        start_min = info["admission"] + timedelta(hours=6)
        start_max = info["exit"] - timedelta(minutes=duration + 120)
        if start_max <= start_min:
            continue
        placed = False
        for _ in range(80):
            room_id = choose(room_candidates)
            main_doc = choose(main_pool)
            offset_hours = random.randint(0, max(1, int((start_max - start_min).total_seconds() // 3600)))
            start = start_min + timedelta(hours=offset_hours)
            start = start.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(minutes=duration)
            if end > info["exit"]:
                continue
            if overlaps(room_schedule[room_id], start, end) or overlaps(doctor_schedule[main_doc], start, end):
                continue
            room_schedule[room_id].append((start, end))
            doctor_schedule[main_doc].append((start, end))
            procedure_rows.append({
                "ProcEventID": proc_event_id,
                "ProcRoomID": room_id,
                "DateTime": start.strftime("%Y-%m-%d %H:%M:%S"),
                "MainDocAMKA": main_doc,
                "ProcedureCode": code,
                "HospitalizationID": hosp["HospitalizationID"],
            })
            assistant_pool = [d for d in dept_doctors if d != main_doc]
            if assistant_pool:
                operates_rows.append({"DoctorAMKA": choose(assistant_pool), "ProcEventID": proc_event_id})
            assists_rows.append({"NurseAMKA": choose(org["nurses_by_department"][info["department"]]), "ProcEventID": proc_event_id})
            helps_rows.append({"AdminStaffAMKA": choose(org["admins_by_department"][info["department"]]), "ProcEventID": proc_event_id})
            proc_event_id += 1
            placed = True
            break
        if not placed:
            continue

    write_csv(output_dir / "procedure_room.csv", ["ProcRoomID", "ProcRoomType", "State"], proc_rooms)
    write_csv(output_dir / "procedure_event.csv", [
        "ProcEventID", "ProcRoomID", "DateTime", "MainDocAMKA", "ProcedureCode", "HospitalizationID",
    ], procedure_rows)
    write_csv(output_dir / "operates_in.csv", ["DoctorAMKA", "ProcEventID"], operates_rows)
    write_csv(output_dir / "assists_in.csv", ["NurseAMKA", "ProcEventID"], assists_rows)
    write_csv(output_dir / "helps_in.csv", ["AdminStaffAMKA", "ProcEventID"], helps_rows)
    return {
        "procedure_room": proc_rooms,
        "procedure_event": procedure_rows,
        "operates_in": operates_rows,
        "assists_in": assists_rows,
        "helps_in": helps_rows,
    }


def build_allergies_and_prescriptions(output_dir: Path, drug_ref: dict, org: dict, patients: dict, clinical: dict) -> dict:
    substance_id_by_name = {row["Name"]: row["ID"] for row in drug_ref["substances"]}
    substance_name_by_id = {row["ID"]: row["Name"] for row in drug_ref["substances"]}
    drug_to_substances: dict[int, set[str]] = defaultdict(set)
    drugs_by_substance: dict[str, list[int]] = defaultdict(list)
    for row in drug_ref["has_substances"]:
        drug_id = int(row["DrugID"])
        name = substance_name_by_id[int(row["SubID"])]
        drug_to_substances[drug_id].add(name)
        drugs_by_substance[name].append(drug_id)

    all_drug_ids = tuple(drug_to_substances)
    if not all_drug_ids:
        raise RuntimeError("No drug-substance mappings are available for prescription generation.")

    patient_ids = [row["AMKA"] for row in patients["patient"]]
    allergy_rows = []
    allergy_by_patient: dict[str, set[str]] = defaultdict(set)
    for patient_amka in random.sample(patient_ids, min(SYNTHETIC_ALLERGY_PATIENT_COUNT, len(patient_ids))):
        for substance in random.sample(list(substance_id_by_name), random.randint(1, 3)):
            allergy_by_patient[patient_amka].add(substance)
    for patient_amka, substances in allergy_by_patient.items():
        for substance in substances:
            allergy_rows.append({"PatientAMKA": patient_amka, "SubstanceID": substance_id_by_name[substance]})

    doctor_by_dept = doctor_pool_by_dept(org)
    prescription_rows = []
    used_unique: set[tuple[str, int, int, str]] = set()
    presc_id = 1
    eligible_cache: dict[frozenset[str], tuple[int, ...]] = {}
    substance_cache: dict[tuple[str, frozenset[str]], tuple[int, ...]] = {}

    def banned_key(patient_amka: str) -> frozenset[str]:
        return frozenset(allergy_by_patient.get(patient_amka, set()))

    def eligible_drugs(patient_amka: str) -> tuple[int, ...]:
        banned = banned_key(patient_amka)
        if not banned:
            return all_drug_ids
        cached = eligible_cache.get(banned)
        if cached is None:
            cached = tuple(drug_id for drug_id in all_drug_ids if drug_to_substances[drug_id].isdisjoint(banned))
            eligible_cache[banned] = cached
        return cached

    def safe_drugs(patient_amka: str, substance: str) -> tuple[int, ...]:
        banned = banned_key(patient_amka)
        cache_key = (substance, banned)
        cached = substance_cache.get(cache_key)
        if cached is None:
            cached = tuple(
                drug_id
                for drug_id in drugs_by_substance.get(substance, [])
                if drug_to_substances[drug_id].isdisjoint(banned)
            )
            substance_cache[cache_key] = cached
        return cached

    def add_prescription(hosp: dict, drug_id: int, start_date: date) -> bool:
        nonlocal presc_id
        info = clinical["hospitalization_meta"][hosp["HospitalizationID"]]
        doctor_amk = choose(doctor_by_dept[info["department"]])
        prescription_date = start_date
        key = (doctor_amk, hosp["HospitalizationID"], drug_id, prescription_date.isoformat())
        if key in used_unique:
            return False
        used_unique.add(key)
        end_date = min(info["exit"].date(), start_date + timedelta(days=random.randint(2, 8)))
        if end_date < start_date:
            end_date = start_date
        prescription_rows.append({
            "PrescriptionID": presc_id,
            "HospitalizationID": hosp["HospitalizationID"],
            "DoctorAMKA": doctor_amk,
            "DrugID": drug_id,
            "Dosage": choose(["1 tablet", "500 mg", "1 vial", "40 mg", "1 capsule"]),
            "frequency": choose(["QD", "BID", "TID", "Q6H", "Q8H"]),
            "PrescriptionDate": prescription_date.isoformat(),
            "StartDate": start_date.isoformat(),
            "EndDate": end_date.isoformat(),
        })
        presc_id += 1
        return True

    hospitalizations = clinical["hospitalization"][:]
    random.shuffle(hospitalizations)
    planted = 0
    for hosp in hospitalizations:
        if planted >= SYNTHETIC_PAIRED_PRESCRIPTION_COUNT:
            break
        info = clinical["hospitalization_meta"][hosp["HospitalizationID"]]
        start_date = min(info["exit"].date(), info["admission"].date() + timedelta(days=1))
        pair = COMMON_SUBSTANCE_PAIRS[planted % len(COMMON_SUBSTANCE_PAIRS)]
        d1 = safe_drugs(hosp["PatientAMKA"], pair[0])
        if not d1:
            continue
        drug1 = choose(d1)
        d2 = tuple(drug_id for drug_id in safe_drugs(hosp["PatientAMKA"], pair[1]) if drug_id != drug1)
        if not d2:
            continue
        ok1 = add_prescription(hosp, drug1, start_date)
        ok2 = add_prescription(hosp, choose(d2), start_date)
        if ok1 and ok2:
            planted += 1

    attempts = 0
    while len(prescription_rows) < SYNTHETIC_PRESCRIPTION_COUNT and attempts < SYNTHETIC_PRESCRIPTION_COUNT * 30:
        attempts += 1
        hosp = choose(hospitalizations)
        info = clinical["hospitalization_meta"][hosp["HospitalizationID"]]
        candidates = eligible_drugs(hosp["PatientAMKA"])
        if not candidates:
            continue
        day_span = max(0, (info["exit"].date() - info["admission"].date()).days)
        start_date = info["admission"].date() + timedelta(days=random.randint(0, day_span))
        add_prescription(hosp, choose(candidates), start_date)

    write_csv(output_dir / "allergic_to.csv", ["PatientAMKA", "SubstanceID"], allergy_rows)
    write_csv(output_dir / "prescription_event.csv", [
        "PrescriptionID", "HospitalizationID", "DoctorAMKA", "DrugID", "Dosage", "frequency", "PrescriptionDate", "StartDate", "EndDate",
    ], prescription_rows)
    return {"allergic_to": allergy_rows, "prescription_event": prescription_rows}


def build_images(output_dir: Path, org: dict, procedures: dict) -> dict:
    rows = []
    image_id = 1

    def add_image(description: str, proc_room: int | str = "", staff: str = "", dept: int | str = "", room: int | str = "", room_dept: int | str = "") -> None:
        nonlocal image_id
        rows.append({
            "ImageID": image_id,
            "ImageURL": f"https://example.org/hospital/images/{image_id:04d}.jpg",
            "ImageDescription": description,
            "ProcRoomId": proc_room,
            "StaffAMKA": staff,
            "DepartmentID": dept,
            "RoomID": room,
            "RoomDepartmentID": room_dept,
        })
        image_id += 1

    for dept in org["department"]:
        add_image(f"{dept['Name']} department image", dept=dept["DepartmentID"])
    for staff in org["staff"][:SYNTHETIC_STAFF_IMAGE_COUNT]:
        add_image(f"Staff portrait for {staff['FirstName']} {staff['LastName']}", staff=staff["AMKA"])
    for room in org["room"][:SYNTHETIC_ROOM_IMAGE_COUNT]:
        add_image(f"Room {room['ID']} department {room['DepartmentID']} image", room=room["ID"], room_dept=room["DepartmentID"])
    for proc_room in procedures["procedure_room"]:
        add_image(f"Procedure room {proc_room['ProcRoomID']} image", proc_room=proc_room["ProcRoomID"])

    write_csv(output_dir / "image.csv", [
        "ImageID", "ImageURL", "ImageDescription", "ProcRoomId", "StaffAMKA", "DepartmentID", "RoomID", "RoomDepartmentID",
    ], rows)
    return {"image": rows}


def write_summary(output_dir: Path, sections: dict[str, dict], seed: int) -> None:
    counts = {}
    for section in sections.values():
        for name, rows in section.items():
            if isinstance(rows, list):
                counts[name] = len(rows)
    summary = {
        "seed": seed,
        "output_dir": str(output_dir),
        "row_counts": counts,
        "requirements_check": {
            "doctors_at_least_80": counts.get("doctor", 0) >= 80,
            "patients_at_least_200": counts.get("patient", 0) >= 200,
            "hospitalizations_at_least_500": counts.get("hospitalization", 0) >= 500,
            "departments_at_least_15": counts.get("department", 0) >= 15,
            "prescriptions_at_least_300": counts.get("prescription_event", 0) >= 300,
            "procedure_rooms_at_least_10": counts.get("procedure_room", 0) >= 10,
            "procedure_events_at_least_150": counts.get("procedure_event", 0) >= 150,
            "lab_events_at_least_200": counts.get("hosp_lab_test", 0) >= 200,
            "richer_patients_at_least_target": counts.get("patient", 0) >= SYNTHETIC_PATIENT_COUNT,
            "richer_hospitalizations_at_least_target": counts.get("hospitalization", 0) >= SYNTHETIC_HOSPITALIZATION_COUNT,
            "richer_procedures_at_least_target": counts.get("procedure_event", 0) >= SYNTHETIC_PROCEDURE_EVENT_COUNT,
            "richer_prescriptions_at_least_target": counts.get("prescription_event", 0) >= SYNTHETIC_PRESCRIPTION_COUNT,
        },
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    project_root = Path(args.project_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else project_root / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    ref = build_reference_tables(project_root, output_dir)
    drug_ref = build_drug_tables(project_root, output_dir)
    org = build_staff_and_departments(output_dir)
    patients = build_patients(output_dir, count=SYNTHETIC_PATIENT_COUNT)
    shifts = build_shifts(output_dir, org)
    clinical = build_hospitalizations(output_dir, ref, org, patients)
    triage = build_triage_events(output_dir, org, patients, clinical)
    labs = build_labs(output_dir, ref, org, clinical)
    procedures = build_procedures(output_dir, ref, org, clinical)
    prescriptions = build_allergies_and_prescriptions(output_dir, drug_ref, org, patients, clinical)
    evaluations = build_evaluations(output_dir, clinical, prescriptions)
    images = build_images(output_dir, org, procedures)

    write_summary(output_dir, {
        "reference": ref,
        "drugs": drug_ref,
        "org": org,
        "patients": patients,
        "shifts": shifts,
        "clinical": clinical,
        "triage": triage,
        "labs": labs,
        "procedures": procedures,
        "prescriptions": prescriptions,
        "evaluations": evaluations,
        "images": images,
    }, args.seed)
    print((output_dir / "dataset_summary.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
