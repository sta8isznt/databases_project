with YearStats as ( 
 select 
    h.PatientAMKA,
    year(h.AdmissionDateTime) as HospitalYear,
    sum(h.ActualDays) as TotalDays
 from Hospitalization h
 group by h.PatientAMKA, YEAR(h.AdmissionDateTime)
 having TotalDays > 15
)

select 
    ys.HospitalYear as `Year`,
    ys.TotalDays as `Total Hospitalization Days`,
    count(ys.PatientAMKA) as `Number of Patients`,
    group_concat(concat(p.FirstName, ' ', p.LastName) separator ' | ') as `Patients`
from YearStats ys
join Patient p on ys.PatientAMKA = p.AMKA
group by ys.HospitalYear, ys.TotalDays
having count(ys.PatientAMKA) > 1
order by ys.HospitalYear desc, ys.TotalDays desc;