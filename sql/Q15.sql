-- Active: 1778170419470@@localhost@3306@HospitalDB
explain analyze
with departmentcnt as (
    select t.EmergencyLevel, d.`Name` as DepartmentName, count(t.TriageID) AS CasesPerDept
    from TriageEvent t
    join Hospitalization h using (HospitalizationID)
    join Department d using (DepartmentID)
    where t.Outcome = 'Accepted'
    group by t.EmergencyLevel, d.Name
),
DepartmentDistribution as (
    select  EmergencyLevel, GROUP_CONCAT(CONCAT(DepartmentName, ': ', CasesPerDept) SEPARATOR ' | ') AS ReferralDistribution
    from departmentcnt
    group by EmergencyLevel
)
select t.EmergencyLevel, count(t.TriageID) AS TotalTriages,
    round(avg(
        case 
            when t.Outcome in ('Accepted', 'Discarded')  then timestampdiff(MINUTE, t.TriageDateTime, t.AssessmentDateTime)
        end
    ), 2) as AvgWaitingTimeMinutes,
    round((sum(case when t.Outcome = 'Accepted' then 1 else 0 end) / 
    sum(case when t.Outcome in ('Accepted', 'Discarded') then 1 else 0 end)) * 100, 2) as AcceptanceRate,
    COALESCE(dd.ReferralDistribution, 'No Admissions') AS DepartmentReferrals
from TriageEvent t
left join DepartmentDistribution dd using (EmergencyLevel)
group by t.EmergencyLevel, dd.ReferralDistribution
order by  t.EmergencyLevel asc; 