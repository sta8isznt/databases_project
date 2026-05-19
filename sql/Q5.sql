-- Q5
-- docs  under 35 age with the most surgical proc as main doc 

select d.amka, d.firstname, d.lastname, d.age, count(pev.proceventid) as totalsurgicalproc
from docinfo d
join procedureevent pev on pev.maindocamka = d.amka
join proceduretype pt on pt.proccode = pev.procedurecode
where pt.proctype = 'Surgical'
and d.age < 35
group by d.amka, d.firstname, d.lastname,d.age
order by totalsurgicalproc desc;
