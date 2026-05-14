with docvolumes as (
    select d.amka,d.firstname,d.lastname,count(pev.proceventid) as totalproc
    from docinfo d
    left join procedureevent pev on pev.maindocamka = d.amka
    and year(pev.`datetime`) = year(curdate())
    group by d.amka,d.firstname,d.lastname
)
select dv.amka,dv.firstname,dv.lastname,totalproc
from docvolumes dv
where totalproc <= (
    select max(totalproc) - 5 from docvolumes
);