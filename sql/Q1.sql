-- Active: 1778170419470@@localhost@3306@HospitalDB
select d.Name, year(h.exitDateTime) as `Year`, c.KENcode, 
    sum(c.BaseCost) as BaseCost,
    sum(
        case
            when h.ActualDays > c.PredictedAvgTime
            then (h.ActualDays - c.PredictedAvgTime) * c.ChargePerDay
            else 0
        end
    ) as ExtraCost,
    sum(
        case
            when h.ActualDays > c.PredictedAvgTime
            then (h.ActualDays - c.PredictedAvgTime) * c.ChargePerDay
            else 0
        end
    ) + sum(c.BaseCost) as TotalRevenue,
    p.InsuranceProviderName,
    count(h.HospitalizationID) as HospitalizationCount
from Hospitalization h
join Department d on h.DepartmentID = d.DepartmentID
join Cost c on h.KENCode = c.KENCode
join Patient p on h.PatientAMKA = p.AMKA
where h.ExitDateTime is not null
group by d.DepartmentID, d.Name, year(h.exitDateTime), c.KENCode, p.InsuranceProviderName;