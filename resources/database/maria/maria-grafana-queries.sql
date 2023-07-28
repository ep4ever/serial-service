--
--  GRAFANA QUERIES
--

-- load gauge
select
	TRUNCATE(SUM(value) / SUM(
		CASE WHEN value > 0 THEN 1 ELSE 0 END
	), 2) AS value
from
	dashboard d
where
	d.identifier = 'load'

-- batt_soc stat
select
	TRUNCATE(SUM(value) / SUM(
		CASE WHEN value > 0 THEN 1 ELSE 0 END
	), 2) AS value
from
	dashboard d
where
	d.identifier = 'batt_soc'

-- batt_voltage stat
select
	TRUNCATE(SUM(value) / SUM(
		CASE WHEN value > 0 THEN 1 ELSE 0 END
	), 2) AS value
from
	dashboard d
where
	d.identifier = 'batt_voltage'

-- kwh/day stat
WITH prod_kwh AS (
SELECT
	truncate(
    	avg(z.value) * timestampdiff(
    		SECOND, min(z.date), max(z.date)
    	) / 3600 / 1000, 2
    ) AS kwh
FROM
	data z
JOIN device d ON
	d.id = z.device_id
JOIN field f ON
	f.id = z.field_id
WHERE
	f.name = 'rated_watt'
	AND date_format(z.date, '%Y-%m-%d') = curdate()
GROUP BY
	d.name
)
SELECT
	sum(kwh) AS value
FROM
	prod_kwh

-- month amount (€) stat
with average as(
select
	truncate(avg(z.value) * timestampdiff(SECOND, min(z.date), max(z.date)) / 3600 / 1000, 2) AS kwh
from
	data z
join device d on
	d.id = z.device_id
join field f on
	f.id = z.field_id
where
	f.name = 'rated_watt'
	and YEAR (z.date) = YEAR(NOW())
group by
	d.name
order by
	MONTH(z.date) DESC,
	d.name
)
select
	CONCAT(TRUNCATE(sum(kwh) * 0.2, 2), ' €')
from
	average;

-- temperature stat
select
	TRUNCATE(SUM(value) / SUM(
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
	UNIX_TIMESTAMP(z.`date`) AS `time`,
	d.name,
	z.value
FROM
	data AS z
JOIN device d ON
	d.id = z.device_id
JOIN field f ON
	f.id = z.field_id
WHERE
	DATE_FORMAT(z.`date`, '%Y-%m-%d') = CURDATE()
	AND f.name = 'rated_watt'
	AND d.name IN('6420an', '3210an', '3910bp')
order by
	z.`date` DESC
