-- We consider a hospitalization to belong to a doctor only when the doctor is
-- the MainDocAMK of at least one ProcedureEvent during that hospitalization.
-- For this query we examine the doctor with AMK = '10000000000'.

select d.AMKA, s.`FirstName`, s.`LastName`, avg(e.`QoDoctorS`) as AverageDoctorService, avg(e.`GeneralExperience`) as AverageGeneralExperience
from Doctor d
join ActiveStaff s using(`AMKA`)
join ProcedureEvent pe on pe.`MainDocAMKA` = d.`AMKA`
join `Hospitalization` h using(`HospitalizationID`)
join `Evaluation` e using(`HospitalizationID`)
where d.AMKA = '10000000000'
group by d.`AMKA`, s.`FirstName`, s.`LastName`;  