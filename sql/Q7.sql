select s.`Name`, count(distinct a.`PatientAMKA`) as TotalPatients, count(distinct h.`DrugID`) as TotalDrugs
from `Substances` s
left join allergic_to a on s.`ID` = a.`SubstanceID`
left join `HasSubstances` h on h.`SubID` = s.`ID`
group by s.`ID`, s.`Name`
order by TotalPatients desc;