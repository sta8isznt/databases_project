-- For this query we examine the doctor with AMKA = '10000000000'.

SELECT de.DoctorAMKA, s.FirstName, s.LastName,
    ROUND(AVG(de.QoDoctorS), 2) AS AvgDoctorQuality,
    ROUND(AVG(he.GeneralExperience), 2) AS AvgHospitalExperience
FROM DoctorEvaluation de
JOIN HospEvaluation he ON de.HospitalizationID = he.HospitalizationID
JOIN ActiveStaff s ON de.DoctorAMKA = s.AMKA
WHERE de.DoctorAMKA = '10000000000' 
GROUP BY de.DoctorAMKA, s.FirstName, s.LastName;
