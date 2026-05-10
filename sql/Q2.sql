-- specialty = 'Cardiology'
-- AMK, FistName, LastName, yes or no if had shift the cur year.# procedures as surgeon 

with shiftcnt as (
    select doctoramk, count(*) as shifttotal
    from hasdoctor
    where year(shiftdate) = year(curdate())
    group by doctoramk
),
    surgcnt as (
    select pev.maindocamk, count(pev.proceventid) as surgtotal
    from procedureevent pev
    join proceduretype pt on pev.procedurecode = pt.proccode
    where pt.proctype = 'Surgical'
    and year(pev.datetime) = year(curdate())
    group by pev.maindocamk
)
select d.amk, d.firstname, d.lastname, 
    case when coalesce(shc.shifttotal,0) > 0 then 'yes' else 'no' end as hadshift,
    coalesce(sc.surgtotal,0) as totalprocedures
    from docinfo d
    left join shiftcnt shc on d.amk = shc.doctoramk
    left join surgcnt sc on d.amk = sc.maindocamk
    where d.specialty = 'Cardiology'; -- Example specialty, change as needed

