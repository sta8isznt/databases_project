from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from typing import Any, Sequence

import pandas as pd
import streamlit as st

from db import (
    DatabaseConfig,
    admit_new_patient,
    calculate_bill,
    call_returning_df,
    execute,
    execute_transaction,
    fetch_df as db_fetch_df,
    fetch_scalar_options as db_fetch_scalar_options,
    generate_shifts,
    rows_as_options as db_rows_as_options,
)
from queries import (
    PARAMETERIZED_SQL,
    QUERY_TITLES,
    available_query_files,
    is_read_only_sql,
    load_sql,
)


st.set_page_config(page_title="HospitalDB", layout="wide")


def configured_database() -> DatabaseConfig:
    with st.sidebar:
        st.header("Database")
        host = st.text_input("Host", value=os.getenv("MYSQL_HOST", "127.0.0.1"))
        port = st.number_input(
            "Port", min_value=1, max_value=65535, value=int(os.getenv("MYSQL_PORT", "3306"))
        )
        database = st.text_input("Database", value=os.getenv("MYSQL_DATABASE", "HospitalDB"))
        user = st.text_input("User", value=os.getenv("MYSQL_USER", "root"))
        password = st.text_input(
            "Password", value=os.getenv("MYSQL_PASSWORD", ""), type="password"
        )
    return DatabaseConfig(host=host, port=int(port), user=user, password=password, database=database)


def run_read_query(
    config: DatabaseConfig,
    sql: str,
    params: Sequence[Any] | None = None,
    title: str | None = None,
) -> pd.DataFrame:
    try:
        df = db_fetch_df(config, sql, params)
    except Exception as exc:
        st.error(str(exc))
        return pd.DataFrame()

    if title:
        st.subheader(title)
    if df.empty:
        st.info("No rows returned.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
    return df


def safe_fetch_df(
    config: DatabaseConfig,
    sql: str,
    params: Sequence[Any] | None = None,
) -> pd.DataFrame:
    try:
        return db_fetch_df(config, sql, params)
    except Exception as exc:
        st.error(str(exc))
        return pd.DataFrame()


def fetch_scalar_options(
    config: DatabaseConfig,
    sql: str,
    params: Sequence[Any] | None = None,
) -> list[Any]:
    try:
        return db_fetch_scalar_options(config, sql, params)
    except Exception as exc:
        st.error(str(exc))
        return []


def rows_as_options(
    config: DatabaseConfig,
    sql: str,
    label_columns: Sequence[str],
    value_column: str,
    params: Sequence[Any] | None = None,
) -> list[tuple[str, Any]]:
    try:
        return db_rows_as_options(config, sql, label_columns, value_column, params)
    except Exception as exc:
        st.error(str(exc))
        return []


def run_write_action(config: DatabaseConfig, sql: str, params: Sequence[Any]) -> bool:
    try:
        execute(config, sql, params)
    except Exception as exc:
        show_database_error(exc)
        return False
    else:
        st.success("Database action completed.")
        return True


def run_transaction_action(
    config: DatabaseConfig,
    statements: Sequence[tuple[str, Sequence[Any] | None]],
) -> bool:
    try:
        execute_transaction(config, statements)
    except Exception as exc:
        show_database_error(exc)
        return False
    else:
        st.success("Database action completed.")
        return True


def run_direct_new_patient_admission(
    config: DatabaseConfig,
    patient: dict[str, Any],
    room_id: int,
    department_id: int,
    ken_code: str,
    admission_datetime: datetime,
) -> bool:
    try:
        admit_new_patient(
            config,
            patient,
            room_id,
            department_id,
            ken_code,
            admission_datetime,
        )
    except Exception as exc:
        show_database_error(exc)
        return False
    else:
        st.success("New patient registered and admitted.")
        return True


def run_generate_shifts_action(
    config: DatabaseConfig,
    start_date: date,
    end_date: date,
    department_id: int | None,
) -> bool:
    try:
        inserted = generate_shifts(config, start_date, end_date, department_id)
    except Exception as exc:
        show_database_error(exc)
        return False
    else:
        st.success(f"Generated {inserted} missing shift rows.")
        return True


def show_database_error(exc: Exception) -> None:
    message = str(exc)
    if "chk_triage_outcome" in message:
        st.error(
            "The live database still has the old triage check constraint. "
            "Run the triage constraint migration so Pending rows can enter the priority queue."
        )
        st.code(
            """
ALTER TABLE TriageEvent DROP CHECK chk_triage_outcome;

ALTER TABLE TriageEvent
ADD CONSTRAINT chk_triage_outcome CHECK (
    (Outcome = 'Pending' AND HospitalizationID IS NULL AND AssessmentDateTime IS NULL) OR
    (Outcome = 'Accepted' AND HospitalizationID IS NOT NULL AND AssessmentDateTime IS NOT NULL) OR
    (Outcome = 'Discarded' AND HospitalizationID IS NULL AND AssessmentDateTime IS NOT NULL)
);
""".strip(),
            language="sql",
        )
    else:
        st.error(message)


def option_value(options: list[tuple[str, Any]], label: str) -> Any | None:
    return next((value for item_label, value in options if item_label == label), None)


def no_options(message: str) -> bool:
    st.info(message)
    return True


def combine_date_time(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock)


def get_departments(config: DatabaseConfig) -> list[tuple[str, int]]:
    return rows_as_options(
        config,
        "SELECT DepartmentID, Name FROM Department ORDER BY Name",
        ["Name", "DepartmentID"],
        "DepartmentID",
    )


def get_available_rooms(config: DatabaseConfig, department_id: int) -> list[tuple[str, int]]:
    return rows_as_options(
        config,
        """
        SELECT ID, Type, State
        FROM Room
        WHERE DepartmentID = %s AND State = 'Available'
        ORDER BY ID
        """,
        ["ID", "Type"],
        "ID",
        (department_id,),
    )


def page_dashboard(config: DatabaseConfig) -> None:
    st.title("HospitalDB")

    if st.button("Test connection"):
        run_read_query(config, "SELECT DATABASE() AS CurrentDatabase, NOW() AS ServerTime")

    counts = run_read_query(
        config,
        """
        SELECT 'Departments' AS Entity, COUNT(*) AS Total FROM Department
        UNION ALL SELECT 'Staff', COUNT(*) FROM Staff
        UNION ALL SELECT 'Doctors', COUNT(*) FROM Doctor
        UNION ALL SELECT 'Nurses', COUNT(*) FROM Nurse
        UNION ALL SELECT 'Admin staff', COUNT(*) FROM AdminStaff
        UNION ALL SELECT 'Patients', COUNT(*) FROM Patient
        UNION ALL SELECT 'Hospitalizations', COUNT(*) FROM Hospitalization
        UNION ALL SELECT 'Triage events', COUNT(*) FROM TriageEvent
        UNION ALL SELECT 'Procedure events', COUNT(*) FROM ProcedureEvent
        UNION ALL SELECT 'Prescriptions', COUNT(*) FROM PrescriptionEvent
        """,
        title="Core Data Volume",
    )
    if not counts.empty:
        metric_cols = st.columns(min(5, len(counts)))
        for idx, row in counts.head(5).iterrows():
            metric_cols[idx % len(metric_cols)].metric(row["Entity"], int(row["Total"]))

    dept_tab, shift_tab, queue_tab = st.tabs(["Departments", "Shift Alerts", "Patient Queue"])

    with dept_tab:
        run_read_query(
            config,
            "SELECT * FROM DepartmentInfo ORDER BY DepartmentName",
            title="Departments",
        )

    with shift_tab:
        run_read_query(
            config,
            "SELECT * FROM ShiftsAlerts ORDER BY ShiftDate, DepartmentName, ShiftTypeName LIMIT 100",
            title="Shift Alerts",
        )

    with queue_tab:
        st.subheader("Patient Priority Queue")
        queue = safe_fetch_df(
            config,
            """
            SELECT *
            FROM PatientQueue
            LIMIT 25
            """,
        )
        if queue.empty:
            st.info("The priority queue is empty. No triaged patients are waiting for a doctor decision.")
        else:
            st.dataframe(queue, width="stretch", hide_index=True)

        waiting_by_level = run_read_query(
            config,
            """
            SELECT EmergencyLevel, COUNT(*) AS WaitingPatients
            FROM PatientQueue
            GROUP BY EmergencyLevel
            ORDER BY EmergencyLevel
            """,
            title="Waiting Patients by Priority",
        )
        if not waiting_by_level.empty:
            st.bar_chart(waiting_by_level.set_index("EmergencyLevel")["WaitingPatients"])

        triage_history = run_read_query(
            config,
            """
            SELECT EmergencyLevel, Outcome, COUNT(*) AS Cases
            FROM TriageEvent
            GROUP BY EmergencyLevel, Outcome
            ORDER BY EmergencyLevel, Outcome
            """,
            title="Triage History by Emergency Level and Outcome",
        )
        if not triage_history.empty:
            chart_data = triage_history.pivot(
                index="EmergencyLevel", columns="Outcome", values="Cases"
            ).fillna(0)
            st.bar_chart(chart_data)


def query_parameter_inputs(
    config: DatabaseConfig,
    filename: str,
) -> tuple[str, Sequence[Any]]:
    if filename == "Q2.sql":
        specialties = fetch_scalar_options(
            config, "SELECT DISTINCT Specialty FROM Doctor ORDER BY Specialty"
        )
        specialty = st.selectbox("Specialty", specialties or ["Cardiology"])
        return PARAMETERIZED_SQL[filename], (specialty,)

    if filename == "Q4.sql":
        doctors = rows_as_options(
            config,
            """
            SELECT d.AMKA, s.FirstName, s.LastName, d.Specialty
            FROM Doctor d
            JOIN Staff s ON d.AMKA = s.AMKA
            ORDER BY s.LastName, s.FirstName
            """,
            ["LastName", "FirstName", "Specialty", "AMKA"],
            "AMKA",
        )
        selected = st.selectbox("Doctor", [label for label, _ in doctors] or ["10000000000"])
        amk = option_value(doctors, selected) or selected
        return PARAMETERIZED_SQL[filename], (amk,)

    if filename == "Q6.sql":
        patients = rows_as_options(
            config,
            """
            SELECT AMKA, FirstName, LastName
            FROM Patient
            ORDER BY LastName, FirstName
            LIMIT 500
            """,
            ["LastName", "FirstName", "AMKA"],
            "AMKA",
        )
        selected = st.selectbox("Patient", [label for label, _ in patients] or ["30000000000"])
        amka = option_value(patients, selected) or selected
        return PARAMETERIZED_SQL[filename], (amka,)

    if filename == "Q8.sql":
        departments = fetch_scalar_options(config, "SELECT Name FROM Department ORDER BY Name")
        shift_date = st.date_input("Date", value=date.today())
        department = st.selectbox("Department", departments or ["Cardiology"])
        return PARAMETERIZED_SQL[filename], (
            shift_date,
            department,
            shift_date,
            department,
            shift_date,
            department,
        )

    if filename == "Q12.sql":
        week_start = st.date_input("Week start", value=date.today())
        week_end = st.date_input("Week end", value=week_start + timedelta(days=6))
        return PARAMETERIZED_SQL[filename], (
            week_start,
            week_end,
            week_start,
            week_end,
            week_start,
            week_end,
        )

    return load_sql(filename), ()


def page_queries(config: DatabaseConfig) -> None:
    st.title("Assignment Queries")
    query_files = available_query_files()
    filename = st.selectbox(
        "Query",
        query_files,
        format_func=lambda name: f"{name}: {QUERY_TITLES.get(name, name)}",
    )

    sql, params = query_parameter_inputs(config, filename)
    edited_sql = st.text_area("SQL", value=sql.strip(), height=360)

    col1, col2 = st.columns([1, 5])
    with col1:
        run = st.button("Run query", type="primary")
    with col2:
        st.caption("The guided inputs use raw SQL parameters. The text area is editable for ad-hoc demo queries.")

    if run:
        if not is_read_only_sql(edited_sql):
            st.error("The query runner only executes read-only SQL. Use workflow pages for writes.")
            return
        run_read_query(config, edited_sql, params)


def page_triage(config: DatabaseConfig) -> None:
    st.title("Triage Workflow")
    st.caption(
        "Flow: patient arrives, triage is recorded immediately, the patient waits in the priority FIFO queue, then a doctor accepts or discards the case."
    )
    if notice := st.session_state.pop("triage_notice", None):
        st.success(notice)

    queue_sql = """
        SELECT
            t.TriageID,
            p.AMKA,
            p.FirstName,
            p.LastName,
            t.EmergencyLevel,
            t.TriageDateTime,
            t.Symptoms
        FROM TriageEvent t
        JOIN Patient p ON t.PatientAMKA = p.AMKA
        WHERE t.Outcome = 'Pending'
        ORDER BY t.EmergencyLevel, t.TriageDateTime
    """
    queue = run_read_query(config, queue_sql, title="Patients Waiting for Doctor Decision")

    if st.button("Doctor fetch next patient"):
        try:
            df = call_returning_df(config, "FetchNext")
        except Exception as exc:
            st.error(str(exc))
        else:
            if df.empty:
                st.info("No patient is currently waiting in the priority queue.")
            else:
                st.session_state["fetched_triage_id"] = int(df.iloc[0]["TriageID"])
                st.session_state["triage_workflow"] = "Doctor accepts"
                st.dataframe(df, width="stretch", hide_index=True)

    departments = get_departments(config)
    triage_ids = queue["TriageID"].tolist() if not queue.empty and "TriageID" in queue else []

    workflow = st.radio(
        "Workflow step",
        ["Record triage and enqueue", "Doctor accepts", "Doctor discards"],
        horizontal=True,
        key="triage_workflow",
    )

    if workflow == "Record triage and enqueue":
        patients = rows_as_options(
            config,
            """
            SELECT AMKA, FirstName, LastName
            FROM Patient
            WHERE IsActive = 1
            ORDER BY LastName, FirstName
            LIMIT 500
            """,
            ["LastName", "FirstName", "AMKA"],
            "AMKA",
        )
        insurance_providers = fetch_scalar_options(
            config, "SELECT Name FROM InsuranceProvider ORDER BY Name"
        )
        nurses = rows_as_options(
            config,
            """
            SELECT n.AMKA, s.FirstName, s.LastName, n.Rank
            FROM Nurse n
            JOIN Staff s ON n.AMKA = s.AMKA
            WHERE s.IsActive = 1
            ORDER BY s.LastName, s.FirstName
            """,
            ["LastName", "FirstName", "Rank", "AMKA"],
            "AMKA",
        )

        patient_source = st.radio(
            "Patient source",
            ["Existing patient", "New patient"],
            horizontal=True,
            key="triage_patient_source",
        )

        with st.form("create_triage_event"):
            patient_amka = None
            new_patient_fields: dict[str, Any] = {}
            if patient_source == "Existing patient":
                patient_label = (
                    st.selectbox("Patient", [label for label, _ in patients])
                    if patients
                    else None
                )
                patient_amka = option_value(patients, patient_label)
                if not patients:
                    st.info("No active patients are available.")
            else:
                st.markdown("**New patient**")
                patient_amka = st.text_input("AMKA")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    first_name = st.text_input("First name")
                with col_b:
                    last_name = st.text_input("Last name")
                with col_c:
                    father_name = st.text_input("Father name")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    birth_date = st.date_input("Birth date", value=date(1990, 1, 1))
                with col_b:
                    gender = st.selectbox("Gender", ["M", "F"])
                with col_c:
                    nationality = st.text_input("Nationality", value="Greek")

                col_a, col_b = st.columns(2)
                with col_a:
                    weight = st.number_input("Weight kg", min_value=0.1, max_value=999.9, value=70.0, step=0.1)
                with col_b:
                    height = st.number_input("Height cm", min_value=0.1, max_value=999.9, value=170.0, step=0.1)

                address = st.text_input("Address")
                col_a, col_b = st.columns(2)
                with col_a:
                    email = st.text_input("Email")
                with col_b:
                    profession = st.text_input("Profession")
                insurance_provider = (
                    st.selectbox("Insurance provider", insurance_providers)
                    if insurance_providers
                    else None
                )
                if not insurance_providers:
                    st.info("No insurance providers are available.")

                new_patient_fields = {
                    "amka": patient_amka,
                    "first_name": first_name,
                    "last_name": last_name,
                    "father_name": father_name,
                    "birth_date": birth_date,
                    "gender": gender,
                    "weight": weight,
                    "height": height,
                    "address": address,
                    "email": email or None,
                    "profession": profession or None,
                    "nationality": nationality,
                    "insurance_provider": insurance_provider,
                }

            nurse_label = (
                st.selectbox("Triage nurse", [label for label, _ in nurses])
                if nurses
                else None
            )
            nurse_amk = option_value(nurses, nurse_label)
            emergency_level = st.slider("Emergency level", min_value=1, max_value=5, value=3)
            symptoms = st.text_area("Symptoms", value="")
            triage_day = st.date_input("Arrival date", value=date.today())
            triage_time = st.time_input(
                "Arrival time",
                value=datetime.now().time().replace(microsecond=0),
                key="create_triage_time",
            )
            if not nurses:
                st.info("No active nurses are available.")
            new_patient_ready = (
                patient_source == "New patient"
                and patient_amka
                and first_name
                and last_name
                and father_name
                and address
                and nationality
                and insurance_provider
            )
            existing_patient_ready = patient_source == "Existing patient" and patient_amka
            submitted = st.form_submit_button(
                "Add patient to priority queue",
                disabled=not (nurse_amk and (existing_patient_ready or new_patient_ready)),
            )

        if submitted and patient_source == "Existing patient":
            if run_write_action(
                config,
                """
                INSERT INTO TriageEvent
                    (Symptoms, EmergencyLevel, Outcome, TriageDateTime, HospitalizationID,
                     AssessmentDateTime, PatientAMKA, NurseAMKA)
                VALUES (%s, %s, 'Pending', %s, NULL, NULL, %s, %s)
                """,
                (
                    symptoms or None,
                    emergency_level,
                    combine_date_time(triage_day, triage_time),
                    patient_amka,
                    nurse_amk,
                ),
            ):
                st.session_state["triage_notice"] = "Patient added to the priority queue."
                st.rerun()
        elif submitted:
            if run_transaction_action(
                config,
                [
                    (
                        """
                        INSERT INTO Patient
                            (AMKA, FirstName, LastName, FatherName, BirthDate, Gender,
                             Weight, Height, Address, Email, Profession, Nationality,
                             InsuranceProviderName)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            new_patient_fields["amka"],
                            new_patient_fields["first_name"],
                            new_patient_fields["last_name"],
                            new_patient_fields["father_name"],
                            new_patient_fields["birth_date"],
                            new_patient_fields["gender"],
                            new_patient_fields["weight"],
                            new_patient_fields["height"],
                            new_patient_fields["address"],
                            new_patient_fields["email"],
                            new_patient_fields["profession"],
                            new_patient_fields["nationality"],
                            new_patient_fields["insurance_provider"],
                        ),
                    ),
                    (
                        """
                        INSERT INTO TriageEvent
                            (Symptoms, EmergencyLevel, Outcome, TriageDateTime, HospitalizationID,
                             AssessmentDateTime, PatientAMKA, NurseAMKA)
                        VALUES (%s, %s, 'Pending', %s, NULL, NULL, %s, %s)
                        """,
                        (
                            symptoms or None,
                            emergency_level,
                            combine_date_time(triage_day, triage_time),
                            new_patient_fields["amka"],
                            nurse_amk,
                        ),
                    ),
                ],
            ):
                st.session_state["triage_notice"] = "New patient registered and added to the priority queue."
                st.rerun()

    elif workflow == "Doctor accepts":
        ken_codes = fetch_scalar_options(
            config, "SELECT KENCode FROM Cost ORDER BY KENCode LIMIT 500"
        )
        with st.form("triage_admission"):
            fetched_triage_id = st.session_state.get("fetched_triage_id")
            triage_index = (
                triage_ids.index(fetched_triage_id)
                if fetched_triage_id in triage_ids
                else 0
            )
            triage_id = (
                st.selectbox("Triage event", triage_ids, index=triage_index)
                if triage_ids
                else None
            )
            dept_label = (
                st.selectbox("Department", [label for label, _ in departments])
                if departments
                else None
            )
            department_id = option_value(departments, dept_label)
            rooms = get_available_rooms(config, int(department_id)) if department_id else []
            room_label = (
                st.selectbox("Available room", [label for label, _ in rooms])
                if rooms
                else None
            )
            room_id = option_value(rooms, room_label)
            ken_code = st.selectbox("KEN code", ken_codes) if ken_codes else None
            if not triage_ids:
                st.info("No pending triage events are available.")
            if department_id and not rooms:
                st.info("No available rooms in the selected department.")
            if not ken_codes:
                st.info("No KEN codes are available.")
            admission_day = st.date_input("Admission date", value=date.today())
            admission_time = st.time_input("Admission time", value=datetime.now().time().replace(microsecond=0))
            submitted = st.form_submit_button(
                "Process admission",
                disabled=not all([triage_id, department_id, room_id, ken_code]),
            )

        if submitted:
            if run_write_action(
                config,
                "CALL ProcessTriageAdmission(%s, %s, %s, %s, %s)",
                (
                    triage_id,
                    room_id,
                    department_id,
                    ken_code,
                    combine_date_time(admission_day, admission_time),
                ),
            ):
                st.session_state.pop("fetched_triage_id", None)
                st.session_state["triage_notice"] = "Patient accepted. The waiting queue has been refreshed."
                st.rerun()

    else:
        with st.form("triage_discard"):
            fetched_triage_id = st.session_state.get("fetched_triage_id")
            triage_index = (
                triage_ids.index(fetched_triage_id)
                if fetched_triage_id in triage_ids
                else 0
            )
            discard_id = (
                st.selectbox("Triage event to discard", triage_ids, index=triage_index)
                if triage_ids
                else None
            )
            if not triage_ids:
                st.info("No pending triage events are available.")
            assessment_day = st.date_input("Assessment date", value=date.today())
            assessment_time = st.time_input(
                "Assessment time",
                value=datetime.now().time().replace(microsecond=0),
                key="discard_time",
            )
            submitted = st.form_submit_button("Discard patient", disabled=discard_id is None)

        if submitted:
            if run_write_action(
                config,
                "CALL DiscardTriagePatient(%s, %s)",
                (discard_id, combine_date_time(assessment_day, assessment_time)),
            ):
                st.session_state.pop("fetched_triage_id", None)
                st.session_state["triage_notice"] = "Patient discarded. The waiting queue has been refreshed."
                st.rerun()


def page_hospitalizations(config: DatabaseConfig) -> None:
    st.title("Hospitalizations")
    if notice := st.session_state.pop("hospitalization_notice", None):
        st.success(notice)

    run_read_query(
        config,
        """
        SELECT
            h.HospitalizationID,
            h.PatientAMKA,
            p.FirstName,
            p.LastName,
            d.Name AS Department,
            h.RoomID,
            h.AdmissionDateTime,
            h.ExitDateTime,
            h.KENCode
        FROM Hospitalization h
        JOIN Patient p ON h.PatientAMKA = p.AMKA
        JOIN Department d ON h.DepartmentID = d.DepartmentID
        ORDER BY h.AdmissionDateTime DESC
        LIMIT 100
        """,
        title="Recent Hospitalizations",
    )

    departments = get_departments(config)

    admit_tab, discharge_tab, bill_tab = st.tabs(["Admit patient", "Discharge patient", "Calculate bill"])

    with admit_tab:
        patients = rows_as_options(
            config,
            """
            SELECT AMKA, FirstName, LastName
            FROM Patient
            WHERE IsActive = 1
            ORDER BY LastName, FirstName
            LIMIT 500
            """,
            ["LastName", "FirstName", "AMKA"],
            "AMKA",
        )
        insurance_providers = fetch_scalar_options(
            config, "SELECT Name FROM InsuranceProvider ORDER BY Name"
        )
        ken_codes = fetch_scalar_options(config, "SELECT KENCode FROM Cost ORDER BY KENCode LIMIT 500")
        patient_source = st.radio(
            "Patient source",
            ["Existing patient", "New direct-admission patient"],
            horizontal=True,
            key="hospitalization_patient_source",
        )
        with st.form("admit_patient"):
            patient_amka = None
            new_patient_fields: dict[str, Any] = {}
            if patient_source == "Existing patient":
                patient_label = (
                    st.selectbox("Patient", [label for label, _ in patients])
                    if patients
                    else None
                )
                patient_amka = option_value(patients, patient_label)
                if not patients:
                    st.info("No active patients are available.")
            else:
                st.markdown("**New direct-admission patient**")
                patient_amka = st.text_input("AMKA", key="direct_admit_amka")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    first_name = st.text_input("First name", key="direct_admit_first_name")
                with col_b:
                    last_name = st.text_input("Last name", key="direct_admit_last_name")
                with col_c:
                    father_name = st.text_input("Father name", key="direct_admit_father_name")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    birth_date = st.date_input(
                        "Birth date",
                        value=date(1990, 1, 1),
                        key="direct_admit_birth_date",
                    )
                with col_b:
                    gender = st.selectbox("Gender", ["M", "F"], key="direct_admit_gender")
                with col_c:
                    nationality = st.text_input(
                        "Nationality",
                        value="Greek",
                        key="direct_admit_nationality",
                    )

                col_a, col_b = st.columns(2)
                with col_a:
                    weight = st.number_input(
                        "Weight kg",
                        min_value=0.1,
                        max_value=999.9,
                        value=70.0,
                        step=0.1,
                        key="direct_admit_weight",
                    )
                with col_b:
                    height = st.number_input(
                        "Height cm",
                        min_value=0.1,
                        max_value=999.9,
                        value=170.0,
                        step=0.1,
                        key="direct_admit_height",
                    )

                address = st.text_input("Address", key="direct_admit_address")
                col_a, col_b = st.columns(2)
                with col_a:
                    email = st.text_input("Email", key="direct_admit_email")
                with col_b:
                    profession = st.text_input("Profession", key="direct_admit_profession")
                insurance_provider = (
                    st.selectbox(
                        "Insurance provider",
                        insurance_providers,
                        key="direct_admit_insurance_provider",
                    )
                    if insurance_providers
                    else None
                )
                if not insurance_providers:
                    st.info("No insurance providers are available.")

                new_patient_fields = {
                    "amka": patient_amka,
                    "first_name": first_name,
                    "last_name": last_name,
                    "father_name": father_name,
                    "birth_date": birth_date,
                    "gender": gender,
                    "weight": weight,
                    "height": height,
                    "address": address,
                    "email": email or None,
                    "profession": profession or None,
                    "nationality": nationality,
                    "insurance_provider": insurance_provider,
                }

            dept_label = (
                st.selectbox("Department", [label for label, _ in departments], key="admit_dept")
                if departments
                else None
            )
            department_id = option_value(departments, dept_label)
            rooms = get_available_rooms(config, int(department_id)) if department_id else []
            room_label = (
                st.selectbox("Available room", [label for label, _ in rooms], key="admit_room")
                if rooms
                else None
            )
            room_id = option_value(rooms, room_label)
            ken_code = st.selectbox("KEN code", ken_codes, key="admit_ken") if ken_codes else None
            if department_id and not rooms:
                st.info("No available rooms in the selected department.")
            if not ken_codes:
                st.info("No KEN codes are available.")
            admission_day = st.date_input("Admission date", value=date.today(), key="admit_date")
            admission_time = st.time_input(
                "Admission time",
                value=datetime.now().time().replace(microsecond=0),
                key="admit_time",
            )
            existing_patient_ready = patient_source == "Existing patient" and patient_amka
            new_patient_ready = (
                patient_source == "New direct-admission patient"
                and patient_amka
                and first_name
                and last_name
                and father_name
                and address
                and nationality
                and insurance_provider
            )
            submitted = st.form_submit_button(
                "Admit",
                disabled=not all(
                    [
                        department_id,
                        room_id,
                        ken_code,
                        existing_patient_ready or new_patient_ready,
                    ]
                ),
            )

        if submitted and patient_source == "Existing patient":
            if run_write_action(
                config,
                "CALL AdmitPatient(%s, %s, %s, %s, %s)",
                (
                    patient_amka,
                    room_id,
                    department_id,
                    ken_code,
                    combine_date_time(admission_day, admission_time),
                ),
            ):
                st.session_state["hospitalization_notice"] = "Existing patient admitted."
                st.rerun()
        elif submitted:
            if run_direct_new_patient_admission(
                config,
                new_patient_fields,
                int(room_id),
                int(department_id),
                ken_code,
                combine_date_time(admission_day, admission_time),
            ):
                st.session_state["hospitalization_notice"] = "New direct-admission patient registered and admitted."
                st.rerun()

    with discharge_tab:
        open_hospitalizations = rows_as_options(
            config,
            """
            SELECT h.HospitalizationID, p.FirstName, p.LastName, h.AdmissionDateTime
            FROM Hospitalization h
            JOIN Patient p ON h.PatientAMKA = p.AMKA
            WHERE h.ExitDateTime IS NULL
            ORDER BY h.AdmissionDateTime
            """,
            ["HospitalizationID", "LastName", "FirstName", "AdmissionDateTime"],
            "HospitalizationID",
        )
        with st.form("discharge_patient"):
            hosp_label = (
                st.selectbox("Open hospitalization", [label for label, _ in open_hospitalizations])
                if open_hospitalizations
                else None
            )
            if not open_hospitalizations:
                st.info("No open hospitalizations are available.")
            hospitalization_id = option_value(open_hospitalizations, hosp_label)
            exit_day = st.date_input("Exit date", value=date.today())
            exit_time = st.time_input(
                "Exit time",
                value=datetime.now().time().replace(microsecond=0),
                key="exit_time",
            )
            submitted = st.form_submit_button("Discharge", disabled=hospitalization_id is None)

        if submitted:
            run_write_action(
                config,
                "CALL DischargePatient(%s, %s)",
                (hospitalization_id, combine_date_time(exit_day, exit_time)),
            )

    with bill_tab:
        hospitalization_ids = fetch_scalar_options(
            config,
            "SELECT HospitalizationID FROM Hospitalization ORDER BY HospitalizationID DESC LIMIT 500",
        )
        hospitalization_id = (
            st.selectbox("Hospitalization", hospitalization_ids)
            if hospitalization_ids
            else None
        )
        if not hospitalization_ids:
            st.info("No hospitalizations are available.")
        if st.button("Calculate bill"):
            if hospitalization_id is None:
                st.info("Select a hospitalization first.")
                return
            try:
                bill = calculate_bill(config, int(hospitalization_id))
            except Exception as exc:
                st.error(str(exc))
            else:
                st.metric("Additional fees", bill.get("AdditionalFees", 0))
                st.metric("Total fees", bill.get("TotalFees", 0))


def page_staff_shifts(config: DatabaseConfig) -> None:
    st.title("Staff and Shifts")
    if notice := st.session_state.pop("shift_notice", None):
        st.success(notice)
    run_read_query(
        config,
        "SELECT * FROM ShiftsAlerts ORDER BY ShiftDate, DepartmentName, ShiftTypeName LIMIT 100",
        title="Shift Alerts",
    )

    generate_tab, register_tab, assign_tab = st.tabs(
        ["Generate shifts", "Register staff", "Assign shift"]
    )
    departments = get_departments(config)

    with generate_tab:
        st.caption("Create the required Morning, Afternoon, and Night shift rows for each selected date.")
        with st.form("generate_shifts"):
            start_day = st.date_input("Start date", value=date.today(), key="shift_gen_start")
            end_day = st.date_input(
                "End date",
                value=date.today() + timedelta(days=6),
                key="shift_gen_end",
            )
            department_labels = ["All departments"] + [label for label, _ in departments]
            department_label = st.selectbox("Department", department_labels)
            selected_department_id = (
                None
                if department_label == "All departments"
                else option_value(departments, department_label)
            )
            if not departments:
                st.info("No departments are available.")
            if end_day < start_day:
                st.error("End date must be on or after start date.")
            day_count = (end_day - start_day).days + 1
            if day_count > 62:
                st.warning("This will generate shifts for more than two months.")
            submitted = st.form_submit_button(
                "Generate missing shifts",
                disabled=not departments or end_day < start_day,
            )

        if submitted:
            if run_generate_shifts_action(
                config,
                start_day,
                end_day,
                int(selected_department_id) if selected_department_id is not None else None,
            ):
                st.session_state["shift_notice"] = "Missing shifts generated. Shift lists have been refreshed."
                st.rerun()

        preview_department_sql = (
            "AND DepartmentID = %s" if selected_department_id is not None else ""
        )
        preview_params: tuple[Any, ...] = (
            (start_day, end_day, selected_department_id)
            if selected_department_id is not None
            else (start_day, end_day)
        )
        run_read_query(
            config,
            f"""
            SELECT Date, ShiftTypeName, COUNT(*) AS ShiftRows
            FROM Shift
            WHERE Date BETWEEN %s AND %s
              {preview_department_sql}
            GROUP BY Date, ShiftTypeName
            ORDER BY Date, ShiftTypeName
            """,
            preview_params,
            title="Existing Generated Shifts in Selected Range",
        )

    with register_tab:
        staff_type = st.radio("Staff type", ["Doctor", "Nurse", "AdminStaff"], horizontal=True)
        with st.form("register_staff"):
            amk = st.text_input("AMKA")
            first_name = st.text_input("First name")
            last_name = st.text_input("Last name")
            birth_date = st.date_input("Birth date", value=date(1990, 1, 1))
            email = st.text_input("Email")
            hire_date = st.date_input("Hire date", value=date.today())

            if staff_type == "Doctor":
                license_no = st.text_input("License")
                specialty = st.text_input("Specialty")
                rank = st.selectbox("Rank", ["Resident", "Registrar", "Consultant", "Director"])
                supervisors = rows_as_options(
                    config,
                    """
                    SELECT d.AMKA, s.FirstName, s.LastName, d.Rank
                    FROM Doctor d
                    JOIN Staff s ON d.AMKA = s.AMKA
                    ORDER BY s.LastName, s.FirstName
                    """,
                    ["LastName", "FirstName", "Rank", "AMKA"],
                    "AMKA",
                )
                supervisor_labels = ["None"] + [label for label, _ in supervisors]
                supervisor_label = st.selectbox("Supervisor", supervisor_labels)
                supervisor_amk = None if supervisor_label == "None" else option_value(supervisors, supervisor_label)
            elif staff_type == "Nurse":
                rank = st.selectbox("Rank", ["AssistantNurse", "Nurse", "HeadNurse"])
                dept_label = (
                    st.selectbox("Department", [label for label, _ in departments])
                    if departments
                    else None
                )
                if not departments:
                    st.info("No departments are available.")
                department_id = option_value(departments, dept_label)
            else:
                role = st.text_input("Role")
                office = st.text_input("Office")
                dept_label = (
                    st.selectbox("Department", [label for label, _ in departments])
                    if departments
                    else None
                )
                if not departments:
                    st.info("No departments are available.")
                department_id = option_value(departments, dept_label)

            submitted = st.form_submit_button(
                "Register",
                disabled=staff_type in {"Nurse", "AdminStaff"} and department_id is None,
            )

        if submitted and staff_type == "Doctor":
            run_write_action(
                config,
                "CALL RegisterDoctor(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    amk,
                    first_name,
                    last_name,
                    birth_date,
                    email or None,
                    hire_date,
                    license_no,
                    specialty,
                    rank,
                    supervisor_amk,
                ),
            )
        elif submitted and staff_type == "Nurse":
            run_write_action(
                config,
                "CALL RegisterNurse(%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    amk,
                    first_name,
                    last_name,
                    birth_date,
                    email or None,
                    hire_date,
                    rank,
                    department_id,
                ),
            )
        elif submitted:
            run_write_action(
                config,
                "CALL RegisterAdminStaff(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    amk,
                    first_name,
                    last_name,
                    birth_date,
                    email or None,
                    hire_date,
                    role,
                    office,
                    department_id,
                ),
            )

    with assign_tab:
        staff_kind = st.radio("Assignment type", ["Doctor", "Nurse", "Admin"], horizontal=True)
        shift_df = safe_fetch_df(
            config,
            """
            SELECT s.DepartmentID, d.Name, s.ShiftTypeName, s.Date
            FROM Shift s
            JOIN Department d ON s.DepartmentID = d.DepartmentID
            ORDER BY s.Date DESC, d.Name, s.ShiftTypeName
            LIMIT 500
            """,
        )
        with st.form("assign_shift"):
            shift_labels = [
                f"{row.Date} - {row.Name} - {row.ShiftTypeName}"
                for row in shift_df.itertuples()
            ] if not shift_df.empty else []
            shift_label = st.selectbox("Shift", shift_labels) if shift_labels else None
            if not shift_labels:
                st.info("No shifts are available.")
            if shift_label and not shift_df.empty:
                shift_index = shift_labels.index(shift_label)
                shift_row = shift_df.iloc[shift_index]
            else:
                shift_row = None

            if staff_kind == "Doctor":
                staff_options = rows_as_options(
                    config,
                    """
                    SELECT d.AMKA, s.FirstName, s.LastName, d.Specialty
                    FROM Doctor d
                    JOIN Staff s ON d.AMKA = s.AMKA
                    WHERE s.IsActive = 1
                    ORDER BY s.LastName, s.FirstName
                    """,
                    ["LastName", "FirstName", "Specialty", "AMKA"],
                    "AMKA",
                )
            elif staff_kind == "Nurse":
                staff_options = rows_as_options(
                    config,
                    """
                    SELECT n.AMKA, s.FirstName, s.LastName, n.Rank
                    FROM Nurse n
                    JOIN Staff s ON n.AMKA = s.AMKA
                    WHERE s.IsActive = 1
                    ORDER BY s.LastName, s.FirstName
                    """,
                    ["LastName", "FirstName", "Rank", "AMKA"],
                    "AMKA",
                )
            else:
                staff_options = rows_as_options(
                    config,
                    """
                    SELECT a.AMKA, s.FirstName, s.LastName, a.Role
                    FROM AdminStaff a
                    JOIN Staff s ON a.AMKA = s.AMKA
                    WHERE s.IsActive = 1
                    ORDER BY s.LastName, s.FirstName
                    """,
                    ["LastName", "FirstName", "Role", "AMKA"],
                    "AMKA",
                )
            staff_label = (
                st.selectbox("Staff member", [label for label, _ in staff_options])
                if staff_options
                else None
            )
            if not staff_options:
                st.info("No active staff members are available for this category.")
            staff_amk = option_value(staff_options, staff_label)
            submitted = st.form_submit_button(
                "Assign",
                disabled=shift_row is None or staff_amk is None,
            )

        if submitted and shift_row is not None:
            if staff_kind == "Doctor":
                sql = "INSERT INTO hasDoctor (DepartmentID, ShiftTypeName, ShiftDate, DoctorAMKA) VALUES (%s, %s, %s, %s)"
            elif staff_kind == "Nurse":
                sql = "INSERT INTO hasNurse (DepartmentID, ShiftTypeName, ShiftDate, NurseAMKA) VALUES (%s, %s, %s, %s)"
            else:
                sql = "INSERT INTO hasAdmin (DepartmentID, ShiftTypeName, ShiftDate, AdminAMKA) VALUES (%s, %s, %s, %s)"
            run_write_action(
                config,
                sql,
                (
                    int(shift_row["DepartmentID"]),
                    shift_row["ShiftTypeName"],
                    shift_row["Date"],
                    staff_amk,
                ),
            )


def page_prescriptions(config: DatabaseConfig) -> None:
    st.title("Prescription Safety")

    hospitalizations = rows_as_options(
        config,
        """
        SELECT h.HospitalizationID, p.FirstName, p.LastName, h.AdmissionDateTime
        FROM Hospitalization h
        JOIN Patient p ON h.PatientAMKA = p.AMKA
        ORDER BY h.AdmissionDateTime DESC
        LIMIT 500
        """,
        ["HospitalizationID", "LastName", "FirstName", "AdmissionDateTime"],
        "HospitalizationID",
    )
    doctors = rows_as_options(
        config,
        """
        SELECT d.AMKA, s.FirstName, s.LastName, d.Specialty
        FROM Doctor d
        JOIN Staff s ON d.AMKA = s.AMKA
        WHERE s.IsActive = 1
        ORDER BY s.LastName, s.FirstName
        """,
        ["LastName", "FirstName", "Specialty", "AMKA"],
        "AMKA",
    )

    if not hospitalizations:
        st.info("No hospitalizations are available.")
        return
    if not doctors:
        st.info("No active doctors are available.")
        return

    with st.form("prescription"):
        hosp_label = st.selectbox("Hospitalization", [label for label, _ in hospitalizations])
        hospitalization_id = option_value(hospitalizations, hosp_label)
        doctor_label = st.selectbox("Doctor", [label for label, _ in doctors])
        doctor_amk = option_value(doctors, doctor_label)
        drug_id = st.number_input("Drug ID", min_value=1, step=1)
        dosage = st.text_input("Dosage", value="1 tablet")
        frequency = st.text_input("Frequency", value="twice daily")
        prescription_date = st.date_input("Prescription date", value=date.today())
        start_date = st.date_input("Start date", value=date.today())
        end_date = st.date_input("End date", value=date.today() + timedelta(days=7))
        submitted = st.form_submit_button("Create prescription")

    if hospitalization_id:
        run_read_query(
            config,
            """
            SELECT s.Name AS Allergy
            FROM Hospitalization h
            JOIN allergic_to a ON h.PatientAMKA = a.PatientAMKA
            JOIN Substances s ON a.SubstanceID = s.ID
            WHERE h.HospitalizationID = %s
            ORDER BY s.Name
            """,
            (hospitalization_id,),
            title="Recorded allergies for selected hospitalization",
        )

    if submitted:
        run_write_action(
            config,
            """
            INSERT INTO PrescriptionEvent
                (HospitalizationID, DoctorAMKA, DrugID, Dosage, Frequency, PrescriptionDate, StartDate, EndDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                hospitalization_id,
                doctor_amk,
                int(drug_id),
                dosage,
                frequency,
                prescription_date,
                start_date,
                end_date,
            ),
        )


def page_media(config: DatabaseConfig) -> None:
    st.title("Images and Catalogs")
    run_read_query(
        config,
        """
        SELECT
            ImageID,
            ImageDescription,
            ImageURL,
            COALESCE(StaffAMKA, DepartmentID, ProcRoomID, RoomID) AS TargetID,
            CASE
                WHEN StaffAMKA IS NOT NULL THEN 'Staff'
                WHEN DepartmentID IS NOT NULL THEN 'Department'
                WHEN ProcRoomID IS NOT NULL THEN 'ProcedureRoom'
                WHEN RoomID IS NOT NULL THEN 'Room'
            END AS TargetType
        FROM Image
        ORDER BY ImageID
        LIMIT 100
        """,
        title="Image Records",
    )
    col1, col2 = st.columns(2)
    with col1:
        run_read_query(
            config,
            "SELECT KENCode, Description, BaseCost, PredictedAvgTime, ChargePerDay FROM Cost LIMIT 100",
            title="KEN Catalog Sample",
        )
    with col2:
        run_read_query(
            config,
            "SELECT DrugID, Name, Route, AuthCountry, AuthHolder FROM DrugType LIMIT 100",
            title="Drug Catalog Sample",
        )


def main() -> None:
    config = configured_database()
    pages = {
        "Dashboard": page_dashboard,
        "Queries Q1-Q15": page_queries,
        "Triage": page_triage,
        "Hospitalizations": page_hospitalizations,
        "Staff and Shifts": page_staff_shifts,
        "Prescription Safety": page_prescriptions,
        "Images and Catalogs": page_media,
    }
    selected = st.sidebar.radio("Page", list(pages))
    pages[selected](config)


if __name__ == "__main__":
    main()
