from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Iterable, Mapping, Sequence

import mysql.connector
import pandas as pd


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


def connect(config: DatabaseConfig) -> mysql.connector.MySQLConnection:
    return mysql.connector.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
    )


def fetch_df(
    config: DatabaseConfig,
    sql: str,
    params: Sequence[Any] | None = None,
) -> pd.DataFrame:
    with connect(config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params or ())
            rows = cursor.fetchall() if cursor.with_rows else []
    return pd.DataFrame(rows)


def execute(
    config: DatabaseConfig,
    sql: str,
    params: Sequence[Any] | None = None,
) -> int:
    with connect(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            rowcount = cursor.rowcount
        conn.commit()
    return rowcount


def execute_transaction(
    config: DatabaseConfig,
    statements: Sequence[tuple[str, Sequence[Any] | None]],
) -> None:
    with connect(config) as conn:
        try:
            with conn.cursor() as cursor:
                for sql, params in statements:
                    cursor.execute(sql, params or ())
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def call_returning_df(
    config: DatabaseConfig,
    procedure_name: str,
    params: Sequence[Any] | None = None,
) -> pd.DataFrame:
    with connect(config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.callproc(procedure_name, params or ())
            frames = []
            for result in cursor.stored_results():
                frames.append(pd.DataFrame(result.fetchall()))
        conn.commit()
    return frames[0] if frames else pd.DataFrame()


def calculate_bill(config: DatabaseConfig, hospitalization_id: int) -> dict[str, Any]:
    with connect(config) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "CALL CalculateHospitalizationBill(%s, @additional_fees, @total_fees)",
                (hospitalization_id,),
            )
            cursor.execute(
                "SELECT @additional_fees AS AdditionalFees, @total_fees AS TotalFees"
            )
            result = cursor.fetchone() or {}
    return result


def admit_new_patient(
    config: DatabaseConfig,
    patient: Mapping[str, Any],
    room_id: int,
    department_id: int,
    ken_code: str,
    admission_datetime: Any,
) -> None:
    with connect(config) as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Patient
                        (AMKA, FirstName, LastName, FatherName, BirthDate, Gender,
                         Weight, Height, Address, Email, Profession, Nationality,
                         InsuranceProviderName)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        patient["amka"],
                        patient["first_name"],
                        patient["last_name"],
                        patient["father_name"],
                        patient["birth_date"],
                        patient["gender"],
                        patient["weight"],
                        patient["height"],
                        patient["address"],
                        patient["email"],
                        patient["profession"],
                        patient["nationality"],
                        patient["insurance_provider"],
                    ),
                )
                cursor.execute(
                    """
                    SELECT State
                    FROM Room
                    WHERE ID = %s AND DepartmentID = %s
                    FOR UPDATE
                    """,
                    (room_id, department_id),
                )
                room = cursor.fetchone()
                if room is None:
                    raise ValueError("The selected room does not exist.")
                if room[0] != "Available":
                    raise ValueError("The selected room is not available for admission.")

                cursor.execute(
                    """
                    UPDATE Room
                    SET State = 'Occupied'
                    WHERE ID = %s AND DepartmentID = %s
                    """,
                    (room_id, department_id),
                )
                cursor.execute(
                    """
                    INSERT INTO Hospitalization
                        (AdmissionDateTime, PatientAMKA, RoomID, DepartmentID, KENCode)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        admission_datetime,
                        patient["amka"],
                        room_id,
                        department_id,
                        ken_code,
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def generate_shifts(
    config: DatabaseConfig,
    start_date: Any,
    end_date: Any,
    department_id: int | None = None,
) -> int:
    inserted = 0
    current = start_date

    with connect(config) as conn:
        try:
            with conn.cursor() as cursor:
                while current <= end_date:
                    cursor.execute(
                        """
                        INSERT IGNORE INTO Shift (DepartmentID, ShiftTypeName, Date)
                        SELECT d.DepartmentID, st.Name, %s
                        FROM Department d
                        CROSS JOIN ShiftType st
                        WHERE %s IS NULL OR d.DepartmentID = %s
                        """,
                        (current, department_id, department_id),
                    )
                    inserted += max(cursor.rowcount, 0)
                    current = current + timedelta(days=1)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return inserted


def fetch_scalar_options(
    config: DatabaseConfig,
    sql: str,
    params: Sequence[Any] | None = None,
) -> list[Any]:
    df = fetch_df(config, sql, params)
    if df.empty:
        return []
    return df.iloc[:, 0].dropna().tolist()


def rows_as_options(
    config: DatabaseConfig,
    sql: str,
    label_columns: Iterable[str],
    value_column: str,
    params: Sequence[Any] | None = None,
) -> list[tuple[str, Any]]:
    df = fetch_df(config, sql, params)
    if df.empty:
        return []

    options: list[tuple[str, Any]] = []
    labels = list(label_columns)
    for _, row in df.iterrows():
        label = " - ".join(str(row[col]) for col in labels if col in row)
        options.append((label, row[value_column]))
    return options
