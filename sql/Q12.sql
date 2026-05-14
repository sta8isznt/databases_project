select
    hd.ShiftDate as `Date`,
    hd.ShiftTypeName as `ShiftType`,
    dep.Name as `Department`,
    'Doctor' as `StaffCategory`,
    d.Specialty as `SubClass`,
    count(hd.DoctorAMKA) as `StaffCount`
from hasDoctor hd
join doctor d on hd.DoctorAMKA = d.AMKA
join department dep on hd.DepartmentID = dep.DepartmentID
where hd.ShiftDate between '2026-03-10' and '2026-03-17'
group by hd.ShiftDate, hd.ShiftTypeName, dep.Name, d.Specialty

union all

select
    hn.ShiftDate,
    hn.ShiftTypeName,
    dep.Name,
    'Nurse',
    n.Rank,
    count(hn.NurseAMKA)
from hasNurse hn
join nurse n on hn.NurseAMKA = n.AMKA
join department dep on hn.DepartmentID = dep.DepartmentID
where hn.ShiftDate between '2026-03-10' and '2026-03-17'
group by hn.ShiftDate, hn.ShiftTypeName, dep.Name, n.Rank

union all

select
    ha.ShiftDate,
    ha.ShiftTypeName,
    dep.Name,
    'Admin',
    a.Role,
    count(ha.AdminAMKA)
from hasAdmin ha
join AdminStaff a on ha.AdminAMKA = a.AMKA
join department dep on ha.DepartmentID = dep.DepartmentID
where ha.ShiftDate between '2026-03-10' and '2026-03-17'
group by ha.ShiftDate, ha.ShiftTypeName, dep.Name, a.Role
order by `Date`, `Department`, `ShiftType`, `StaffCategory`;