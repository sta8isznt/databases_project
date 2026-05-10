select count(t.triageid) as total_triages,
avg(
    case
        when t.outcome = 'Accepted' or t.outcome = 'Discarded' then t.assesmentdatetime - t.triagedatetime
    end
) as avg_waiting_time,
count(
    case
        when t.outcome = 'Accepted' then 1
        when t.outcome = 'Discarded' then 0
        else null
    end
) / count(
   case
        when t.outcome = 'Accepted' then 1
        when t.outcome = 'Discarded' then 1
        else null
    end 
) as acceptance_rate,
count(
    case
        when t.outcome = 'Accepted' then 1
        else null
    end
) as total_accepted
from triageevent t
join hospitalization h using(hospitalizationid)
join department d using(departmentid)
group by t.emergencylevel,t.departmentid;