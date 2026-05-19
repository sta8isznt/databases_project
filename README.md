# HospitalDB

HospitalDB is a MySQL/MariaDB database project for a hospital information
system. It includes the relational schema, constraints, triggers, stored
procedures, views, indexes, synthetic/reference data, assignment SQL queries,
and a small Streamlit UI that demonstrates the database without using an ORM.

## Quick Start

Run all commands from the project root. Replace `/path/to/databases_project`
with the actual project folder on your machine.

```bash
cd /path/to/databases_project
```

If the `mysql` command is available in your terminal, create the schema and load
the dataset with:

```bash
mysql -u root -p < sql/install.sql
mysql --local-infile=1 -u root -p < sql/load.sql
```

If you use MAMP, XAMPP, WAMP, or a MySQL installation where `mysql` is not on
your `PATH`, use the matching command from the platform-specific section below.

Run one of the assignment queries:

```bash
mysql -u root -p HospitalDB < sql/Q1.sql
```

Start the optional Streamlit UI:

```bash
make ui
```

## Prerequisites

- MySQL or MariaDB server.
- MySQL/MariaDB command-line client.
- `LOCAL INFILE` support enabled for loading CSV files.
- Python 3 and `pip`, required for the Streamlit UI and optional data
  regeneration scripts.
- `make`, optional but recommended for running the Streamlit UI with one
  command.

The project uses plain SQL and `mysql-connector-python`; it does not use an ORM.

## MySQL Client Commands By Environment

The setup commands in this README use `mysql` as the command-line client. In
some installations, especially MAMP/XAMPP/WAMP, the client is not globally
available as `mysql`. Use the command that matches your environment.

| Environment | Typical client command | Typical credentials |
|---|---|---|
| Native MySQL/MariaDB on Linux/macOS/Windows, added to `PATH` | `mysql` | User/password chosen during installation |
| Native MySQL on Windows, not added to `PATH` | `"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"` | User/password chosen during installation |
| Native MariaDB on Windows, not added to `PATH` | `"C:\Program Files\MariaDB 11.x\bin\mysql.exe"` | User/password chosen during installation |
| MAMP on macOS, MySQL 8.0 | `/Applications/MAMP/Library/bin/mysql80/bin/mysql -h 127.0.0.1 -P 8889` | Usually `root` / `root` |
| MAMP on macOS, MySQL 5.7 | `/Applications/MAMP/Library/bin/mysql57/bin/mysql -h 127.0.0.1 -P 8889` | Usually `root` / `root` |
| XAMPP on macOS | `/Applications/XAMPP/xamppfiles/bin/mysql -h 127.0.0.1 -P 3306` | Usually `root` / empty password |
| XAMPP on Windows | `C:\xampp\mysql\bin\mysql.exe -h 127.0.0.1 -P 3306` | Usually `root` / empty password |
| XAMPP/LAMPP on Linux | `/opt/lampp/bin/mysql -h 127.0.0.1 -P 3306` | Usually `root` / empty password |
| WAMP on Windows | `C:\wamp64\bin\mysql\<mysql-version>\bin\mysql.exe -h 127.0.0.1 -P 3306` | Usually `root` / empty password |

Add `-u root -p` to whichever client command you use. If your MySQL server uses
a different user, password, host, or port, replace those values accordingly.
The same replacement applies to the query commands later in this README.

Examples:

```bash
# Native MySQL/MariaDB when mysql is on PATH
mysql -u root -p < sql/install.sql
mysql --local-infile=1 -u root -p < sql/load.sql

# MAMP on macOS with MySQL 8.0
/Applications/MAMP/Library/bin/mysql80/bin/mysql -h 127.0.0.1 -P 8889 -u root -p < sql/install.sql
/Applications/MAMP/Library/bin/mysql80/bin/mysql --local-infile=1 -h 127.0.0.1 -P 8889 -u root -p < sql/load.sql

# MAMP on macOS with MySQL 5.7
/Applications/MAMP/Library/bin/mysql57/bin/mysql -h 127.0.0.1 -P 8889 -u root -p < sql/install.sql
/Applications/MAMP/Library/bin/mysql57/bin/mysql --local-infile=1 -h 127.0.0.1 -P 8889 -u root -p < sql/load.sql

# XAMPP on macOS
/Applications/XAMPP/xamppfiles/bin/mysql -h 127.0.0.1 -P 3306 -u root -p < sql/install.sql
/Applications/XAMPP/xamppfiles/bin/mysql --local-infile=1 -h 127.0.0.1 -P 3306 -u root -p < sql/load.sql

# XAMPP/LAMPP on Linux
/opt/lampp/bin/mysql -h 127.0.0.1 -P 3306 -u root -p < sql/install.sql
/opt/lampp/bin/mysql --local-infile=1 -h 127.0.0.1 -P 3306 -u root -p < sql/load.sql
```

Windows Command Prompt examples:

```bat
cd C:\path\to\databases_project
C:\xampp\mysql\bin\mysql.exe -h 127.0.0.1 -P 3306 -u root -p < sql\install.sql
C:\xampp\mysql\bin\mysql.exe --local-infile=1 -h 127.0.0.1 -P 3306 -u root -p < sql\load.sql
```

Windows PowerShell does not reliably support `<` input redirection for native
commands. Use Command Prompt, Git Bash, WSL, or call `cmd /c` from PowerShell:

```powershell
cd C:\path\to\databases_project
cmd /c "C:\xampp\mysql\bin\mysql.exe -h 127.0.0.1 -P 3306 -u root -p < sql\install.sql"
cmd /c "C:\xampp\mysql\bin\mysql.exe --local-infile=1 -h 127.0.0.1 -P 3306 -u root -p < sql\load.sql"
```

For WAMP, replace `C:\xampp\mysql\bin\mysql.exe` with the real WAMP MySQL path,
for example:

```bat
C:\wamp64\bin\mysql\mysql8.0.31\bin\mysql.exe
```

The exact WAMP version folder may differ.

For MAMP on macOS, the exact MySQL client depends on the selected MySQL version.
If the commands above do not match your installation, list the available MAMP
clients with:

```bash
find /Applications/MAMP -path '*/bin/mysql' -type f -print
```

Use the returned path in place of `mysql` in all setup, load, and query
commands. Common MAMP results are:

```bash
/Applications/MAMP/Library/bin/mysql80/bin/mysql
/Applications/MAMP/Library/bin/mysql57/bin/mysql
```

## Project Structure

| Path | Purpose |
|---|---|
| `README.md` | Main documentation, setup guide, assumptions, and design notes. |
| `sql/install.sql` | Creates the `HospitalDB` database, tables, constraints, triggers, stored procedures, views, and indexes. |
| `sql/load.sql` | Loads all CSV files from `data/` into the database. |
| `sql/Q1.sql` ... `sql/Q15.sql` | SQL solutions for the assignment queries. |
| `sql/test.sql` | Extra local testing SQL. |
| `Makefile` | Convenience targets for creating the UI virtual environment and running Streamlit. |
| `data/` | Generated CSV files loaded by `sql/load.sql`. |
| `data/raw_data/` | External source workbooks used by preprocessing scripts. |
| `data/dataset_summary.json` | Dataset counts and minimum-requirement checks. |
| `code/` | Python preprocessing and synthetic-data generation scripts. |
| `code/ui/` | Streamlit UI source code. |
| `docs/` | Project report. |
| `diagrams/` | Database diagram files. |

## Database Setup

`sql/install.sql` drops any existing `HospitalDB` database, creates a fresh one,
and then switches to it. Run it from the project root, using the correct MySQL
client command for your environment:

```bash
mysql -u root -p < sql/install.sql
```

For MAMP/XAMPP/WAMP, apply the same idea with the full client path and the right
port. Example for MAMP with MySQL 8.0:

```bash
/Applications/MAMP/Library/bin/mysql80/bin/mysql -h 127.0.0.1 -P 8889 -u root -p < sql/install.sql
```

## Loading Data

`sql/load.sql` uses relative paths such as `data/diagnosis.csv`, so it must be
run from the project root, using the correct MySQL client command for your
environment:

```bash
mysql --local-infile=1 -u root -p < sql/load.sql
```

If your MySQL/MariaDB server disables local infile loading, enable it for the
server/client and rerun the load step. A typical MySQL client invocation is:

```bash
mysql --local-infile=1 -u root -p
```

Then check the server setting:

```sql
SHOW VARIABLES LIKE 'local_infile';
```

If the value is `OFF`, enable it with a privileged MySQL user and reconnect:

```sql
SET GLOBAL local_infile = 1;
```

## Running Queries

Each assignment query is stored as a separate SQL file under `sql/`.

Run a query and print the result:

```bash
mysql -u root -p HospitalDB < sql/Q1.sql
```

Save the result to an output file:

```bash
mysql -u root -p HospitalDB < sql/Q1.sql > sql/Q1_out.txt
```

Run all query files manually by replacing `Q1.sql` with `Q2.sql` through
`Q15.sql`. For the final assignment submission, create the corresponding
`Qx_out.txt` files if required by the course instructions.

## Streamlit UI

The project includes a small raw-SQL Streamlit interface for demonstrating the
HospitalDB schema, views, stored procedures, triggers, and assignment queries.
Install and load the database before starting the UI.

Recommended: run the UI through the project `Makefile`. This creates a local
`.venv/`, installs `code/ui/requirements.txt`, and starts Streamlit:

```bash
make ui
```

Other UI targets:

```bash
make ui-venv     # create .venv only
make ui-install  # install/update UI requirements
make ui-run      # install requirements and run Streamlit
make ui-clean    # remove .venv
```

On Windows, the `Makefile` uses the Python launcher `py -3` by default. If your
installation exposes Python as `python` instead, run:

```bat
make ui PYTHON=python
```

If `make` is not installed on Windows, use the manual Command Prompt or
PowerShell commands below.

Manual setup without `make`:

On Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r code/ui/requirements.txt
python -m streamlit run code/ui/app.py
```

On Windows Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r code\ui\requirements.txt
.venv\Scripts\python -m streamlit run code\ui\app.py
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r code\ui\requirements.txt
.\.venv\Scripts\python.exe -m streamlit run code\ui\app.py
```

The sidebar reads these optional environment-variable defaults:

```bash
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=HospitalDB
MYSQL_USER=root
MYSQL_PASSWORD=
```

You can also edit the connection fields directly in the Streamlit sidebar.
Use the same host, port, username, and password that worked for the command-line
load step. For example, MAMP commonly uses port `8889`, user `root`, and
password `root`, while XAMPP/WAMP commonly use port `3306`, user `root`, and an
empty password unless you changed it.

## Dataset

The repository already includes loadable CSV files under `data/`. The current
dataset summary is stored in `data/dataset_summary.json` and was generated with
seed `20260507`.

| Dataset area | Current count |
|---|---:|
| Doctors | 300 |
| Nurses | 540 |
| Administrative staff | 180 |
| Departments | 15 |
| Rooms | 750 |
| Patients | 900 |
| Hospitalizations | 3600 |
| Triage events | 4200 |
| Lab-test events | 2600 |
| Procedure rooms | 20 |
| Procedure events | 1200 |
| Prescriptions | 3000 |
| Hospital evaluations | 1841 |
| Doctor evaluations | 2923 |
| Images | 215 |

The dataset satisfies the assignment minimums for doctors, patients,
hospitalizations, departments, prescriptions, procedure rooms, procedure events,
and lab-test events.

## Optional Data Regeneration

The committed CSV files are enough to build and run the project. Regeneration is
optional and should be done from the project root.

Install extra preprocessing dependencies if needed:

```bash
python3 -m pip install --user pandas openpyxl
```

Preprocess reference catalogs from the raw workbooks:

```bash
python3 code/preprocess_procedure_types.py
python3 code/preprocess_lab_tests.py
python3 code/preprocess_article57_drugs.py
```

Generate the operational synthetic dataset:

```bash
python3 code/generate_synthetic_data.py
```

After regenerating CSVs, rebuild and reload the database with `sql/install.sql`
and `sql/load.sql`.

## Assumptions

| # | Assumption | Reason |
|---|---|---|
| 1 | `BirthDate` is stored instead of `Age` for `Staff` and `Patient`. | Age is derived and changes over time, while birth date is stable. |
| 2 | `Staff.Type` is stored in the relational model together with subtype tables `Doctor`, `Nurse`, and `AdminStaff`. | The type value makes subtype validation explicit and is used by triggers to enforce consistency. |
| 3 | A `Department` may exist without any assigned `Nurse` or `AdminStaff`. | This keeps the schema flexible for departments that are initially staffed only by doctors. |
| 4 | A `Room` number is unique only inside its `Department`; `Department.RoomNum()` is derived from the rooms that belong to the department. | This supports modelling `Room` as a weak entity and avoids storing a derived count. |
| 5 | `Doctor.Rank` uses English labels mapped from the assignment values: `Ειδικευόμενος -> Resident`, `Επιμελητής Β΄ -> Registrar`, `Επιμελητής Α΄ -> Consultant`, `Διευθυντής -> Director`. | This keeps rank values shorter and uniform while preserving the assignment semantics. |
| 6 | `Nurse.Rank` uses English labels mapped from the assignment values: `Βοηθός Νοσηλευτή -> AssistantNurse`, `Νοσηλευτής -> Nurse`, `Προϊστάμενος -> HeadNurse`. | This keeps nurse-rank values consistent with the English terminology used in the schema. |
| 7 | `Patient.Weight` is stored in kilograms. | This gives a clear interpretation for decimal weight values. |
| 8 | `Patient.Height` is stored in centimeters. | This gives a clear interpretation for decimal height values. |
| 9 | `Staff.IsActive`, `Patient.IsActive`, and `LabTest.IsActive` represent active/inactive records. | This supports lifecycle management without deleting historical medical data. |
| 10 | `Diagnosis` is a reference table for ICD-based diagnoses. A hospitalization may have multiple admission and exit diagnoses. | This keeps diagnosis data normalized and supports realistic clinical cases. |
| 11 | `TriageEvent` represents the emergency-department workflow. It does not store a department when the value would always be Emergency. | This avoids redundant constant data and matches the rule that emergency arrivals first pass through triage. |
| 12 | `ProcedureEvent.MainDocAMKA` stores the main doctor responsible for the procedure; `operates_in` stores additional doctor participants. | This separates the primary doctor role from assistant doctor participation. |
| 13 | Each `PrescriptionEvent` refers to exactly one drug. Multiple drugs are represented by multiple prescription rows. | This follows the assignment uniqueness rule for `(doctor, patient, drug, start date)`. |
| 14 | `PrescriptionEvent.PrescriptionDate` may differ from `StartDate`. | This distinguishes the issue date from the treatment start date. |
| 15 | `Department` uses surrogate primary key `DepartmentID INT AUTO_INCREMENT`; `Name` remains `UNIQUE NOT NULL`. | Referencing an integer key is smaller and more efficient than propagating a `varchar(30)` key through many foreign keys. |
| 16 | `Hospitalization` uses surrogate primary key `HospitalizationID INT AUTO_INCREMENT`; `(PatientAMKA, AdmissionDateTime)` remains unique. | This avoids propagating a large composite key into related tables such as triage, evaluations, diagnoses, and lab tests. |
| 17 | `Shift` uses the composite primary key `(DepartmentID, ShiftTypeName, Date)`. The shift-assignment tables reference the same business key together with the assigned staff member. | A shift is naturally identified by department, shift type, and date, and this keeps shift assignments directly tied to that business identity. |
| 18 | Some business rules are implemented with triggers instead of `CHECK` constraints. | MySQL cannot express all cross-row/cross-table rules with `CHECK`, so triggers enforce supervision, image exclusivity, allergies, procedure overlaps, shifts, and evaluation timing. |
| 19 | Updates to `Staff.AMKA` are allowed and propagated with `ON UPDATE CASCADE` where appropriate. | This allows correction of identifier-entry mistakes while preserving related records. |
| 20 | Staff specialization is disjoint: each staff member belongs to exactly one of `Doctor`, `Nurse`, or `AdminStaff`. | `Staff.Type` plus subtype triggers prevent inconsistent subtype inserts/updates. |
| 21 | The main doctor of a `ProcedureEvent` cannot be the main doctor of another overlapping procedure. Other participating staff may assist in overlapping events. | This enforces primary-doctor responsibility while allowing flexible assistant participation. |
| 22 | Emergency arrivals create a `TriageEvent` and enter the priority FIFO `PatientQueue`; scheduled/direct admissions may create a `Hospitalization` without triage. | This preserves the emergency workflow while supporting planned admissions. |

## Business Rules

| # | Business Rule | Enforcement |
|---|---|---|
| 1 | A department has exactly one director. | `Department.DirectorAMKA` is `NOT NULL UNIQUE` and references `Doctor`. |
| 2 | The department director must also be assigned to that department. | Enforced through department-management procedures and validation logic. |
| 3 | A doctor cannot supervise themself and supervision cycles are not allowed. | `trg_doctor_before_insert` and `trg_doctor_before_update`. |
| 4 | Resident doctors require a supervisor; directors cannot have a supervisor. | Doctor triggers. |
| 5 | A prescription cannot contain a drug whose substances conflict with the patient's allergies. | Prescription allergy triggers. |
| 6 | Patients may evaluate a hospitalization only after discharge. | Hospital-evaluation triggers. |
| 7 | Patients may evaluate only doctors who prescribed medication during that hospitalization. | Doctor-evaluation triggers. |
| 8 | Two procedures cannot overlap in the same procedure room. | Procedure-overlap triggers. |
| 9 | The same main doctor cannot be assigned to overlapping procedures. | Procedure-overlap triggers. |
| 10 | Shift assignments must satisfy department membership, uniqueness, and staffing-count rules. | Doctor, nurse, and admin shift triggers. |
| 11 | A triage event may reference a hospitalization only for the same patient. | Triage-hospitalization triggers. |
| 12 | Each image references exactly one supported entity type. | Image exclusivity triggers. |

## Views

| View | Purpose |
|---|---|
| `DepartmentInfo` | Department details with director name and derived room count. |
| `ActiveStaff` | Active staff records with derived age. |
| `ActivePatient` | Active patient records with derived age. |
| `ActiveLabTest` | Active lab-test catalog rows. |
| `DocInfo` | Doctor details joined with active staff information. |
| `ShiftsAlerts` | Shifts that do not satisfy required staffing counts. |
| `PatientQueue` | Priority FIFO queue for pending triage cases. |

## Indexes

| Index | Table/columns | Purpose |
|---|---|---|
| `idx_staff_name` | `Staff(LastName, FirstName)` | Speeds up staff lookup by name. |
| `idx_patient_name` | `Patient(LastName, FirstName)` | Speeds up patient lookup by name. |
| `idx_doc_specialty` | `Doctor(Specialty)` | Supports filtering and grouping doctors by specialty. |
| `idx_age` | `Staff(BirthDate)` | Supports age-related staff queries through birth-date filtering. |
| `idx_pat_days_in_hospital` | `Hospitalization(PatientAMKA, AdmissionDateTime, ExitDateTime)` | Supports hospitalization-duration and patient-history queries. |
| `idx_hasdoc_shiftdate` | `hasDoctor(ShiftDate)` | Supports shift scheduling queries for doctors. |
| `idx_hasnurse_shiftdate` | `hasNurse(ShiftDate)` | Supports shift scheduling queries for nurses. |
| `idx_hasadmin_shiftdate` | `hasAdmin(ShiftDate)` | Supports shift scheduling queries for administrative staff. |
| `idx_triage_queue` | `TriageEvent(Outcome, EmergencyLevel, TriageDateTime)` | Supports the pending triage priority FIFO queue. |

## Implemented Triggers

| Trigger | Purpose |
|---|---|
| `trg_doctor_before_insert` | Enforce doctor supervisor rules and prevent supervision cycles on insert. |
| `trg_doctor_before_update` | Enforce doctor supervisor rules and prevent supervision cycles on update. |
| `trg_patient_allergy_check_before_insert` | Prevent prescriptions that conflict with patient allergies. |
| `trg_patient_allergy_check_before_update` | Recheck allergy constraints when prescriptions are updated. |
| `trg_Procedure_Overlap_Insert` | Prevent overlapping procedures in the same room or with the same main doctor. |
| `trg_Procedure_Overlap_Update` | Recheck procedure-overlap constraints on update. |
| `trg_hasdoctor_shift_before_insert` | Enforce doctor shift-assignment rules. |
| `trg_hasdoctor_shift_before_update` | Recheck doctor shift-assignment rules on update. |
| `trg_hasDoctor_prevent_removing_last_senior` | Prevent removing the last senior doctor from a shift when senior coverage is required. |
| `trg_Nurse_Shift_Rules_Insert` | Enforce nurse shift-assignment rules. |
| `trg_Nurse_Shift_Rules_Update` | Recheck nurse shift-assignment rules on update. |
| `trg_Admin_Shift_Rules_Insert` | Enforce admin shift-assignment rules. |
| `trg_Admin_Shift_Rules_Update` | Recheck admin shift-assignment rules on update. |
| `trg_triage_hospitalization_same_patient_insert` | Ensure triage-linked hospitalization belongs to the same patient. |
| `trg_triage_hospitalization_same_patient_update` | Recheck triage-linked hospitalization consistency on update. |
| `trg_image_exclusive_insert` | Ensure each image references exactly one supported entity type. |
| `trg_image_exclusive_update` | Recheck image reference exclusivity on update. |
| `trg_hosp_eval_insert` | Allow hospitalization evaluation only after discharge. |
| `trg_hosp_eval_update` | Recheck hospitalization-evaluation timing on update. |
| `trg_doc_eval_insert` | Allow doctor evaluation only after discharge and only for prescribing doctors. |
| `trg_doc_eval_update` | Recheck doctor-evaluation rules on update. |

## Implemented Procedures

| Procedure | Purpose |
|---|---|
| `RegisterDoctor` | Insert a new doctor and corresponding staff row transactionally. |
| `UpdateDoctorInfo` | Update doctor and staff fields transactionally. |
| `RegisterNurse` | Insert a new nurse and corresponding staff row transactionally. |
| `UpdateNurseInfo` | Update nurse and staff fields transactionally. |
| `RegisterAdminStaff` | Insert a new admin staff member and corresponding staff row transactionally. |
| `UpdateAdminStaffInfo` | Update admin staff and staff fields transactionally. |
| `CreateDepartmentWithDirector` | Create a department and assign its director safely. |
| `UpdateDepartmentWithDirector` | Update department details and director safely. |
| `AdmitPatient` | Create a hospitalization and update room state transactionally. |
| `DischargePatient` | Discharge a patient and free the room transactionally. |
| `CalculateHospitalizationBill` | Calculate hospitalization bill from base cost, extra days, lab tests, and procedures. |
| `FetchNext` | Fetch the next pending triage patient from the priority FIFO queue. |
| `ProcessTriageAdmission` | Admit a patient from triage and update triage outcome. |
| `DiscardTriagePatient` | Mark a pending triage patient as not admitted. |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `CREATE DATABASE HospitalDB` fails | The connected user does not have permission to create/drop databases, or you are connected to the wrong server. | Use a privileged user and verify the host/port/socket before rerunning `sql/install.sql`. |
| `LOAD DATA LOCAL INFILE` is disabled | Client or server local-infile setting is off. | Run the client with `--local-infile=1` and enable `local_infile` on the server if needed. |
| CSV file not found during load | `sql/load.sql` was run from the wrong directory. | Run `mysql --local-infile=1 -u root -p < sql/load.sql` from the project root. |
| PowerShell reports that `<` is reserved | PowerShell input redirection differs from Bash/CMD. | Use Command Prompt, Git Bash, WSL, or the `cmd /c` examples above. |
| Connection refused or wrong server | MySQL is running on a different port, common with MAMP/XAMPP. | Use the correct `-P` port and `-h 127.0.0.1`, then match the same settings in Streamlit. |
| Streamlit cannot connect | Wrong host, port, user, password, or unloaded database. | Check the sidebar connection settings and make sure `HospitalDB` has been created and loaded. |
| Query returns no rows | Dataset was not loaded, or the query depends on a specific populated case. | Re-run `sql/load.sql` and verify row counts in `data/dataset_summary.json`; `Cost` loads 694 unique KEN codes from 701 source rows because duplicate KEN codes are deduplicated during load. |

## Submission Checklist

Before final submission, verify that the deliverable contains the files required
by the assignment:

- `README.md`
- `diagrams/er.pdf`
- `diagrams/relational.pdf`
- `sql/install.sql`
- `sql/load.sql`
- `sql/Q1.sql` through `sql/Q15.sql`
- `sql/Q1_out.txt` through `sql/Q15_out.txt`, if requested
- `docs/report.pdf`
- `code/`, if submitting the Streamlit UI and data-generation scripts

## AI/LLM Usage

AI/LLM assistance was used as a development and documentation aid for parts of
the project, including README restructuring and review of run instructions. The
database design, final implementation choices, validation, and submitted content
remain the responsibility of the project authors.
