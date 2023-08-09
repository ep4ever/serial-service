SET lc_time_names = 'fr_FR';

-- total solar panel production in kwh by month
SELECT
    DATE_FORMAT(datestamp, '%W %d %M') AS jour,
    TRUNCATE(SUM(wh)/1000, 2) AS kWh
FROM day_prod_by_device_view
WHERE MONTH(datestamp) = :monthval
GROUP BY datestamp;
