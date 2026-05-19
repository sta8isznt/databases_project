from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "sql"


QUERY_TITLES = {
    "Q1.sql": "Revenue by department, year, KEN code, and insurer",
    "Q2.sql": "Doctors by specialty with current-year shifts and surgeries",
    "Q3.sql": "Patients hospitalized more than three times in the same department",
    "Q4.sql": "Average doctor and general evaluation for one doctor",
    "Q5.sql": "Young doctors with most surgical procedures",
    "Q6.sql": "Hospitalization history for one patient",
    "Q7.sql": "Allergy and drug counts per active substance",
    "Q8.sql": "Staff without scheduled duty for a date and department",
    "Q9.sql": "Patients with equal yearly hospitalization duration above 15 days",
    "Q10.sql": "Top three co-prescribed active-substance pairs",
    "Q11.sql": "Doctors at least five procedures behind the current-year leader",
    "Q12.sql": "Weekly staffing analysis by department, shift, and subclass",
    "Q13.sql": "Doctor supervision hierarchy",
    "Q14.sql": "ICD-10 categories with equal admissions in consecutive years",
    "Q15.sql": "Triage distribution and referral analytics",
}


def available_query_files() -> list[str]:
    return sorted(
        [path.name for path in SQL_DIR.glob("Q*.sql")],
        key=lambda name: int(re.search(r"Q(\d+)", name).group(1)),
    )


def load_sql(filename: str) -> str:
    return (SQL_DIR / filename).read_text(encoding="utf-8")


PARAMETERIZED_SQL = {
    "Q2.sql": """
WITH shiftcnt AS (
    SELECT DoctorAMKA, COUNT(*) AS ShiftTotal
    FROM hasDoctor
    WHERE YEAR(ShiftDate) = YEAR(CURDATE())
    GROUP BY DoctorAMKA
),
surgcnt AS (
    SELECT pe.MainDocAMKA, COUNT(pe.ProcEventID) AS SurgTotal
    FROM ProcedureEvent pe
    JOIN ProcedureType pt ON pe.ProcedureCode = pt.ProcCode
    WHERE pt.ProcType = 'Surgical'
      AND YEAR(pe.`DateTime`) = YEAR(CURDATE())
    GROUP BY pe.MainDocAMKA
)
SELECT
    d.AMKA,
    d.FirstName,
    d.LastName,
    CASE WHEN COALESCE(sc.ShiftTotal, 0) > 0 THEN 'yes' ELSE 'no' END AS HadShift,
    COALESCE(su.SurgTotal, 0) AS TotalProcedures
FROM DocInfo d
LEFT JOIN shiftcnt sc ON d.AMKA = sc.DoctorAMKA
LEFT JOIN surgcnt su ON d.AMKA = su.MainDocAMKA
WHERE d.Specialty = %s
ORDER BY TotalProcedures DESC, d.LastName, d.FirstName
""",
    "Q4.sql": """
SELECT
    de.DoctorAMKA,
    s.FirstName,
    s.LastName,
    ROUND(AVG(de.QoDoctorS), 2) AS AvgDoctorQuality,
    ROUND(AVG(he.GeneralExperience), 2) AS AvgHospitalExperience
FROM DoctorEvaluation de
JOIN HospEvaluation he ON de.HospitalizationID = he.HospitalizationID
JOIN ActiveStaff s ON de.DoctorAMKA = s.AMKA
WHERE de.DoctorAMKA = %s
GROUP BY de.DoctorAMKA, s.FirstName, s.LastName
""",
    "Q6.sql": """
SELECT
    h.HospitalizationID,
    h.AdmissionDateTime,
    h.ExitDateTime,
    (
        SELECT GROUP_CONCAT(DISTINCT CONCAT(d.ICDCode, ': ', d.Description) SEPARATOR ' | ')
        FROM AdmissionDiagnosis ad
        JOIN Diagnosis d ON ad.ICDCode = d.ICDCode
        WHERE ad.HospitalizationID = h.HospitalizationID
    ) AS ICD_diagnoses,
    (
        c.BaseCost
        + GREATEST(IFNULL(h.ActualDays, DATEDIFF(CURDATE(), h.AdmissionDateTime)) - c.PredictedAvgTime, 0)
        * c.ChargePerDay
    ) AS TotalCost,
    (
        SELECT (dq.AvgDoctorService + he.QoNurseS + he.Cleanliness + he.Food + he.GeneralExperience) / 5.0
        FROM HospEvaluation he
        JOIN (
            SELECT HospitalizationID, AVG(QoDoctorS) AS AvgDoctorService
            FROM DoctorEvaluation
            GROUP BY HospitalizationID
        ) dq USING (HospitalizationID)
        WHERE he.HospitalizationID = h.HospitalizationID
    ) AS AvgRating
FROM Hospitalization h
JOIN Cost c ON h.KENCode = c.KENCode
WHERE h.PatientAMKA = %s
ORDER BY h.AdmissionDateTime
""",
    "Q8.sql": """
WITH scheduled_staff AS (
    SELECT DoctorAMKA AS AMKA
    FROM hasDoctor
    WHERE ShiftDate = %s
      AND DepartmentID = (SELECT DepartmentID FROM Department WHERE Name = %s)
    UNION ALL
    SELECT NurseAMKA AS AMKA
    FROM hasNurse
    WHERE ShiftDate = %s
      AND DepartmentID = (SELECT DepartmentID FROM Department WHERE Name = %s)
    UNION ALL
    SELECT AdminAMKA AS AMKA
    FROM hasAdmin
    WHERE ShiftDate = %s
      AND DepartmentID = (SELECT DepartmentID FROM Department WHERE Name = %s)
)
SELECT s.AMKA, s.FirstName, s.LastName, s.Age, s.Type
FROM ActiveStaff s
WHERE NOT EXISTS (
    SELECT 1
    FROM scheduled_staff sch
    WHERE sch.AMKA = s.AMKA
)
ORDER BY s.Type, s.LastName, s.FirstName
""",
    "Q12.sql": """
SELECT
    hd.ShiftDate AS `Date`,
    hd.ShiftTypeName AS ShiftType,
    dep.Name AS Department,
    'Doctor' AS StaffCategory,
    d.Specialty AS SubClass,
    COUNT(hd.DoctorAMKA) AS StaffCount
FROM hasDoctor hd
JOIN Doctor d ON hd.DoctorAMKA = d.AMKA
JOIN Department dep ON hd.DepartmentID = dep.DepartmentID
WHERE hd.ShiftDate BETWEEN %s AND %s
GROUP BY hd.ShiftDate, hd.ShiftTypeName, dep.Name, d.Specialty

UNION ALL

SELECT
    hn.ShiftDate,
    hn.ShiftTypeName,
    dep.Name,
    'Nurse',
    n.Rank,
    COUNT(hn.NurseAMKA)
FROM hasNurse hn
JOIN Nurse n ON hn.NurseAMKA = n.AMKA
JOIN Department dep ON hn.DepartmentID = dep.DepartmentID
WHERE hn.ShiftDate BETWEEN %s AND %s
GROUP BY hn.ShiftDate, hn.ShiftTypeName, dep.Name, n.Rank

UNION ALL

SELECT
    ha.ShiftDate,
    ha.ShiftTypeName,
    dep.Name,
    'Admin',
    a.Role,
    COUNT(ha.AdminAMKA)
FROM hasAdmin ha
JOIN AdminStaff a ON ha.AdminAMKA = a.AMKA
JOIN Department dep ON ha.DepartmentID = dep.DepartmentID
WHERE ha.ShiftDate BETWEEN %s AND %s
GROUP BY ha.ShiftDate, ha.ShiftTypeName, dep.Name, a.Role
ORDER BY `Date`, Department, ShiftType, StaffCategory
""",
}


def first_sql_keyword(sql: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        lines.append(stripped)
    cleaned = "\n".join(lines).lstrip()
    match = re.match(r"([a-zA-Z]+)", cleaned)
    return match.group(1).lower() if match else ""


def is_read_only_sql(sql: str) -> bool:
    return first_sql_keyword(sql) in {"select", "with", "explain", "show", "describe"}
