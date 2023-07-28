--
--  GRAFANA QUERIES
--

-- load gauge
select
	ROUND(SUM(value) / SUM(
		CASE WHEN value > 0 THEN 1 ELSE 0 END
	), 2) AS value
from
	dashboard d
where
	d.identifier = 'load'

-- batt_soc stat
select
	ROUND(SUM(value) / SUM(
		CASE WHEN value > 0 THEN 1 ELSE 0 END
	), 2) AS value
from
	dashboard d
where
	d.identifier = 'batt_soc'

-- batt_voltage stat
select
	ROUND(SUM(value) / SUM(
		CASE WHEN value > 0 THEN 1 ELSE 0 END
	), 2) AS value
from
	dashboard d
where
	d.identifier = 'batt_voltage'

-- kwh/day stat
WITH prod_wh AS (
SELECT
	avg(z.value) * CAST((unixepoch(max(z.date)) - unixepoch(min(z.date))) as REAL) / CAST(3600 as REAL) as wh
FROM
	data z
JOIN device d ON
	d.id = z.device_id
JOIN field f ON
	f.id = z.field_id
WHERE
	f.name = 'rated_watt'
	AND DATE(z.date) = DATE('now')
GROUP BY
	d.name
)
SELECT
	SUM(wh) as value
FROM
	prod_wh

-- month amount (€) stat
with average as(
select
	avg(z.value) * CAST((unixepoch(max(z.date)) - unixepoch(min(z.date))) as REAL) / CAST(3600 as REAL) as wh
from
	data z
join device d on
	d.id = z.device_id
join field f on
	f.id = z.field_id
where
	f.name = 'rated_watt'
	and strftime('%Y', z.date) = strftime('%Y', DATE('now'))
group by
	d.name
order by
	strftime('%m', z.date) DESC,
	d.name
)
select
	ROUND(
	CAST(
		sum(wh) as REAL
	) /
	CAST(
		1000 as REAL
	) * 0.2,
	2
) || ' €'
from
	average;

-- temperature stat
select
	ROUND(SUM(value) / SUM(
		CASE WHEN value > 0 THEN 1 ELSE 0 END
	), 2) AS value
from
	dashboard d
where
	d.identifier = 'temperature'

-- watt gauge
WITH mysel (device,
value) AS (
SELECT
	device.name,
	data.value
FROM
	data
JOIN device ON
	device.id = data.device_id
WHERE
	data.field_id = 7
ORDER BY
	data.id DESC
LIMIT 3
)
SELECT
	SUM(mysel.value) AS watts
FROM
	mysel;

-- production time series (transform: pepare time series > multi-frame time series)
SELECT
	unixepoch(DATETIME(z.`date`, '-2 hour')) AS `time`,
	d.name,
	z.value
FROM
	data AS z
JOIN device d ON
	d.id = z.device_id
JOIN field f ON
	f.id = z.field_id
WHERE
	DATE(z.`date`) = DATE('now')
	AND f.name = 'rated_watt'
	AND d.name IN('6420an', '3210an', '3910bp')
order by
	z.`date` DESC
