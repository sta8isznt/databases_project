with PrescribedSubstances as (
    select
        pe.`HospitalizationID`,
        pe.`StartDate`,
        pe.`EndDate`,
        hs.`SubID`,
        s.`Name`
    from `PrescriptionEvent` pe
    join `HasSubstances` hs using(`DrugId`)
    join `Substances` s
        on hs.`SubID` = s.`ID`
)
select pe1.Name, pe2.Name, count(*) as TotalOccurances
from `PrescribedSubstances` pe1
join `PrescribedSubstances` pe2
    on pe1.`HospitalizationID` = pe2.`HospitalizationID`
   and pe1.`SubID` < pe2.`SubID`
   and pe1.`StartDate` < coalesce(pe2.`EndDate`, '9999-12-31')
   and pe2.`StartDate` < coalesce(pe1.`EndDate`, '9999-12-31')
group by pe1.SubID, pe2.SubID
order by TotalOccurances desc
limit 3;