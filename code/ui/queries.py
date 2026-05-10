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
    SELECT DoctorAMK, COUNT(*) AS ShiftTotal
    FROM hasDoctor
    WHERE YEAR(ShiftDate) = YEAR(CURDATE())
    GROUP BY DoctorAMK
),
surgcnt AS (
    SELECT pe.MainDocAMK, COUNT(pe.ProcEventID) AS SurgTotal
    FROM ProcedureEvent pe
    JOIN ProcedureType pt ON pe.ProcedureCode = pt.ProcCode
    WHERE pt.ProcType = 'Surgical'
      AND YEAR(pe.`DateTime`) = YEAR(CURDATE())
    GROUP BY pe.MainDocAMK
)
SELECT
    d.AMK,
    d.FirstName,
    d.LastName,
    CASE WHEN COALESCE(sc.ShiftTotal, 0) > 0 THEN 'yes' ELSE 'no' END AS HadShift,
    COALESCE(su.SurgTotal, 0) AS TotalProcedures
FROM DocInfo d
LEFT JOIN shiftcnt sc ON d.AMK = sc.DoctorAMK
LEFT JOIN surgcnt su ON d.AMK = su.MainDocAMK
WHERE d.Specialty = %s
ORDER BY TotalProcedures DESC, d.LastName, d.FirstName
""",
    "Q4.sql": """
SELECT
    d.AMK,
    s.FirstName,
    s.LastName,
    AVG(e.QoDoctorS) AS AverageDoctorService,
    AVG(e.GeneralExperience) AS AverageGeneralExperience
FROM Doctor d
JOIN ActiveStaff s USING (AMK)
JOIN ProcedureEvent pe ON pe.MainDocAMK = d.AMK
JOIN Hospitalization h USING (HospitalizationID)
JOIN Evaluation e USING (HospitalizationID)
WHERE d.AMK = %s
GROUP BY d.AMK, s.FirstName, s.LastName
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
        SELECT (e.QoDoctorS + e.QoNurseS + e.Cleanliness + e.Food + e.GeneralExperience) / 5.0
        FROM Evaluation e
        WHERE e.HospitalizationID = h.HospitalizationID
    ) AS AvgRating
FROM Hospitalization h
JOIN Cost c ON h.KENCode = c.KENCode
WHERE h.PatientAMKA = %s
ORDER BY h.AdmissionDateTime
""",
    "Q8.sql": """
WITH scheduled AS (
    SELECT DoctorAMK AS AMK
    FROM hasDoctor
    WHERE ShiftDate = %s
      AND DepartmentID = (SELECT DepartmentID FROM Department WHERE Name = %s)
    UNION
    SELECT NurseAMK AS AMK
    FROM hasNurse
    WHERE ShiftDate = %s
      AND DepartmentID = (SELECT DepartmentID FROM Department WHERE Name = %s)
    UNION
    SELECT AdminAMK AS AMK
    FROM hasAdmin
    WHERE ShiftDate = %s
      AND DepartmentID = (SELECT DepartmentID FROM Department WHERE Name = %s)
)
SELECT s.AMK, s.FirstName, s.LastName, s.Age, s.Type
FROM ActiveStaff s
WHERE NOT EXISTS (
    SELECT 1
    FROM scheduled sch
    WHERE sch.AMK = s.AMK
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
    COUNT(hd.DoctorAMK) AS StaffCount
FROM hasDoctor hd
JOIN Doctor d ON hd.DoctorAMK = d.AMK
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
    COUNT(hn.NurseAMK)
FROM hasNurse hn
JOIN Nurse n ON hn.NurseAMK = n.AMK
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
    COUNT(ha.AdminAMK)
FROM hasAdmin ha
JOIN AdminStaff a ON ha.AdminAMK = a.AMK
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
