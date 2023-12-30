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

-- cumul money saved (€) stat
WITH avg_watt_by_devices AS (
	WITH rated_watt AS (
		SELECT
			d.name AS device,
			z.value,
			z.date as dates
		FROM
			data z
		JOIN device d ON
			d.id = z.device_id
		JOIN field f ON
			f.id = z.field_id
		WHERE
			f.name = 'rated_watt'
	)
	SELECT
		rw.device,
		AVG(rw.value) AS avg_watt,
		(
			CAST((unixepoch(MAX(rw.dates)) - unixepoch(MIN(rw.dates))) AS REAL) /
			CAST(3600 AS REAL)
		) AS elapsed,
		(
			(
				CAST((unixepoch(max(rw.dates)) - unixepoch(min(rw.dates))) AS REAL) /
				CAST(3600 AS REAL)
			) * AVG(rw.value)
		) AS watt_hour,
		MIN(rw.dates) started_at,
		MAX(rw.dates) ended_at
	FROM
		rated_watt AS rw
	GROUP BY
		DATE(rw.dates),
		rw.device
)
SELECT
	SUM(watt_hour)/ 1000 * 0.2 AS value
FROM
	avg_watt_by_devices;

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
	unixepoch(DATETIME(z.`date`, '-1 hour')) AS `time`,
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
order by
	z.`date` DESC
