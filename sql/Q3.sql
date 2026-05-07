select 
    p.FirstName, 
    p.LastName, 
    d.`Name`, 
    count(h.HospitalizationID) as num_of_visits,
    sum(
        c.BaseCost + 
        (greatest(datediff(ifnull(h.ExitDateTime, curdate()),h.AdmissionDateTime) - c.PredictedAvgTime, 0)
        * c.ChargePerDay)
    ) as total_cost
    
from Hospitalization h
join Patient p on h.PatientAMKA = p.AMKA
join Department d on h.DepartmentID = d.DepartmentID
join Cost c on h.KENcode = c.KENcode

group by p.AMKA, p.FirstName, p.LastName, d.`Name`
having count(h.HospitalizationID) > 3;