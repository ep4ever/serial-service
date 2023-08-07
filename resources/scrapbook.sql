-- total solar panel production in kwh
SELECT
	SUM((
		dd.avgval * 
		(TIMESTAMPDIFF(SECOND, dr.started_at, dr.ended_at) / 3600.0)
	) / 1000) AS kwh
from diary_data dd
join diary dr ON dr.id = dd.diary_id 
join device d ON d.id = dd.device_id 
join field f ON f.id = dd.field_id
where f.name = 'rated_watt'