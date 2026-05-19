with scheduled_staff as (
    select hasdoctor.doctoramka as amka
    from hasdoctor 
    where hasdoctor.shiftdate = '2026-03-10' -- change this date to the desired date
    and hasdoctor.departmentid = (
        select departmentid
        from department
        where `name` = 'Cardiology' -- change this department name to the desired department
    )

    union all

    select hasnurse.nurseamka as amka
    from hasnurse
    where hasnurse.shiftdate = '2026-03-10' -- change this date to the desired date
    and hasnurse.departmentid = (
        select departmentid
        from department
        where `name` = 'Cardiology' -- change this department name to the desired department
    )

    union all

    select hasadmin.adminamka as amka
    from hasadmin
    where hasadmin.shiftdate = '2026-03-10' -- change this date to the desired date
    and hasadmin.departmentid = (
        select departmentid
        from department
        where `name` = 'Cardiology' -- change this department name to the desired department
    ) 
)

select s.amka, s.firstname, s.lastname, s.age, s.`type`
from activestaff s
where not exists (
    select 1
    from scheduled_staff ns
    where ns.amka = s.amka
)
order by s.`type`, s.lastname, s.firstname;
