select
    h.HospitalizationID,
    h.AdmissionDateTime,
    h.ExitDateTime,

    (select group_concat(distinct concat(d.ICDcode, ': ', d.Description) separator ' | ')
    from AdmissionDiagnosis ad
    join Diagnosis d on ad.ICDcode = d.ICDcode
    where ad.HospitalizationID = h.HospitalizationID) as ICD_diagnoses,

    (c.BaseCost +
     greatest(ifnull(h.ActualDays, datediff(curdate(), h.AdmissionDateTime))- c.PredictedAvgTime, 0)
     * c.ChargePerDay) as TotalCost,

    (select (e.QoDoctorS + e.QoNurseS + e.Cleanliness + e.Food + e.GeneralExperience) / 5.0
     from Evaluation e
     where e.HospitalizationID = h.HospitalizationID) as AvgRating

from Hospitalization h
join Cost c on h.KENcode = c.KENcode
where h.PatientAMKA = '30000000000'
order by h.AdmissionDateTime;