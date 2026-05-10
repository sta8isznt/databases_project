with nightshifts as (
    select hasdoctor.doctoramk as amk
    from hasdoctor 
    where hasdoctor.shifttypename = 'Night'
    and hasdoctor.shiftdate = '2024-01-01' -- change this date to the desired date
    and hasdoctor.departmentid = (
        select departmentid
        from department
        where `name` = 'Cardiology' -- change this department name to the desired department
    )

    union all

    select hasnurse.nurseamk as amk
    from hasnurse
    where hasnurse.shifttypename = 'Night'
    and hasnurse.shiftdate = '2024-01-01' -- change this date to the desired date
    and hasnurse.departmentid = (
        select departmentid
        from department
        where `name` = 'Cardiology' -- change this department name to the desired department
    )

    union all

    select hasadmin.adminamk as amk
    from hasadmin
    where hasadmin.shifttypename = 'Night'
    and hasadmin.shiftdate = '2024-01-01' -- change this date to the desired date
    and hasadmin.departmentid = (
        select departmentid
        from department
        where `name` = 'Cardiology' -- change this department name to the desired department
    ) 
)

select s.firstname,s.lastname,s.age,s.`type`
from activestaff s
where not exists (
    select 1
    from nightshifts ns
    where ns.amk = s.amk
);
