-- We consider a hospitalization to belong to a doctor only when the doctor is
-- the MainDocAMK of at least one ProcedureEvent during that hospitalization.
-- For this query we examine the doctor with AMK = '10000000000'.

select d.AMK, s.`FirstName`, s.`LastName`, avg(e.`QoDoctorS`) as AverageDoctorService, avg(e.`GeneralExperience`) as AverageGeneralExperience
from Doctor d
join ActiveStaff s using(`AMK`)
join ProcedureEvent pe on pe.`MainDocAMK` = d.`AMK`
join `Hospitalization` h using(`HospitalizationID`)
join `Evaluation` e using(`HospitalizationID`)
where d.AMK = '10000000000'
group by d.`AMK`, s.`FirstName`, s.`LastName`;  