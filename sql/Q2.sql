-- specialty = 'Cardiology'
-- AMKA, FistName, LastName, yes or no if had shift the cur year.# procedures as surgeon 

with shiftcnt as (
    select doctoramka, count(*) as shifttotal
    from hasdoctor
    where year(shiftdate) = year(curdate())
    group by doctoramka
),
    surgcnt as (
    select pev.maindocamka, count(pev.proceventid) as surgtotal
    from procedureevent pev
    join proceduretype pt on pev.procedurecode = pt.proccode
    where pt.proctype = 'Surgical'
    and year(pev.datetime) = year(curdate())
    group by pev.maindocamka
)
select d.amka, d.firstname, d.lastname, 
    case when coalesce(shc.shifttotal,0) > 0 then 'yes' else 'no' end as hadshift,
    coalesce(sc.surgtotal,0) as totalprocedures
    from docinfo d
    left join shiftcnt shc on d.amka = shc.doctoramka
    left join surgcnt sc on d.amka = sc.maindocamka
    where d.specialty = 'Cardiology' -- Example specialty, change as needed
    order by totalprocedures desc, d.lastname, d.firstname;
