-- specialty = 'Cardiology'
-- AMK, FistName, LastName, yes or no if had shift the cur year.# procedures as surgeon 

with shift_cnt as (
    select d.doctoramk, count
)