with recursive doctor_hierarchy as (
    select
        -- Store the root doctor
        d.AMKA as RootDoctorAMKA,
        concat(d.FirstName, ' ', d.LastName) as RootDoctorName,

        sup.AMKA as CurrentDoctorAMKA,
        concat(sup.FirstName, ' ', sup.LastName) as CurrentDoctorName,
        sup.`Rank` as CurrentDoctorRank,

        1 as `Level`,
        sup.SupervisorAMKA
    from DocInfo d
    join DocInfo sup
        on d.SupervisorAMKA = sup.AMKA

    union all

    select
        h.RootDoctorAMKA,
        h.RootDoctorName,

        sup.AMKA as CurrentDoctorAMKA,
        concat(sup.FirstName, ' ', sup.LastName) as CurrentDoctorName,
        sup.`Rank` as CurrentDoctorRank,

        h.`Level` + 1 as `Level`,
        sup.SupervisorAMKA
    from doctor_hierarchy h
    join DocInfo sup
        on h.SupervisorAMKA = sup.AMKA
)
select *
from doctor_hierarchy
order by RootDoctorAMKA, `Level`;
