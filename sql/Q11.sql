with docvolumes as (
    select d.amk,d.firstname,d.lastname,count(pev.proceventid) as totalproc
    from docinfo d
    left join procedureevent pev on pev.maindocamk = d.amk
    and year(pev.`datetime`) = year(curdate())
    group by d.amk,d.firstname,d.lastname
)
select dv.amk,dv.firstname,dv.lastname,totalproc
from docvolumes dv
where totalproc <= (
    select max(totalproc) - 5 from docvolumes
);