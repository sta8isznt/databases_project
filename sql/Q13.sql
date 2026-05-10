with recursive doctor_hierarchy as (
    select
        -- Store the root doctor
        d.AMK as RootDoctorAMK,
        concat(d.FirstName, ' ', d.LastName) as RootDoctorName,

        d.AMK as CurrentDoctorAMK,
        concat(d.FirstName, ' ', d.LastName) as CurrentDoctorName,
        d.`Rank` as CurrentDoctorRank,

        0 as `Level`,
        d.SupervisorAMK
    from DocInfo d

    union all

    select
        h.RootDoctorAMK,
        h.RootDoctorName,

        sup.AMK as CurrentDoctorAMK,
        concat(sup.FirstName, ' ', sup.LastName) as CurrentDoctorName,
        sup.`Rank` as CurrentDoctorRank,

        h.`Level` + 1 as `Level`,
        sup.SupervisorAMK
    from doctor_hierarchy h
    join DocInfo sup
        on h.SupervisorAMK = sup.AMK
)
select *
from doctor_hierarchy
order by RootDoctorAMK, `Level`;