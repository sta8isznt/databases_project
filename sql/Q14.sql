with YearlyDiagnoses as (
 select
    ad.ICDCode,
    year(h.AdmissionDateTime) as AdmissionYear,
    count(h.HospitalizationID) as TotalCases
 from Hospitalization h
 join AdmissionDiagnosis ad on h.HospitalizationID = ad.HospitalizationID

 group by ad.ICDCode, year(h.AdmissionDateTime)
 having count(h.HospitalizationID) >= 5
)
select
    y1.ICDCode as 'Code ICD-10',
    y1.AdmissionYear as 'Year 1',
    y2.AdmissionYear as 'Year 2',
    y1.TotalCases as 'Same Number of Cases'
from YearlyDiagnoses y1
join YearlyDiagnoses y2 on y1.ICDCode = y2.ICDCode and y1.TotalCases = y2.TotalCases and y1.AdmissionYear = y2.Admissionyear -1
order by y1.AdmissionYear desc, y1.TotalCases desc;      