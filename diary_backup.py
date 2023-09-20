#!/usr/bin/env python

"""
This script must be run via a cron job
after all devices are off
"""

from ast import literal_eval

import MySQLdb
from dotenv import dotenv_values

dconfig = dotenv_values(dotenv_path=".env")
connection = MySQLdb.connect(
    user=dconfig.get('DB_USER'),
    password=dconfig.get('DB_PWD'),
    host=dconfig.get('DB_HOST'),
    database=dconfig.get('DB_NAME')
)

cursor = connection.cursor()
cursor.execute('SELECT id, name, port FROM device')
devices = cursor.fetchall()
deviceDict = dict()
for device in devices:
    deviceDict[device[1]] = device[0]

cursor.execute("""
SELECT id, label, name, category, registeraddr FROM field
""")
fields = cursor.fetchall()
fieldDict = dict()
for field in fields:
    keyval = field[1]
    if field[3] == 'simple':
        fieldDict[keyval] = {
            'id': field[0],
            'kind': 'simple',
            'value': literal_eval(field[4]),
            'fieldname': field[2]
        }
    else:
        data = tuple(field[4].split('|'))
        fieldDict[keyval] = {
            'id': field[0],
            'kind': 'lowhigh',
            'lsb': literal_eval(data[0]),
            'msb': literal_eval(data[1]),
            'fieldname': field[2]
        }

# take the last inserted diary element
cursor.execute("""
SELECT
    id,
    DATE_FORMAT(datestamp, '%Y-%m-%d')
FROM diary ORDER BY id DESC LIMIT 1
""")
diary_info = cursor.fetchone()

diary_id = diary_info[0]
datestamp = diary_info[1]

sql = """
    UPDATE diary SET started_at = (
        SELECT MIN(time(z.date))
        FROM data AS z
        WHERE z.date >= (
            SELECT datestamp FROM diary WHERE id = {}
        ) &&  z.date < ((
            SELECT datestamp FROM diary WHERE id = {}
        ) + INTERVAL 1 DAY)
    ), ended_at = (
        SELECT MAX(time(z.date))
        FROM data AS z
        WHERE z.date >= (
            SELECT datestamp FROM diary WHERE id = {}
        ) &&  z.date < ((
            SELECT datestamp FROM diary WHERE id = {}
        ) + INTERVAL 1 DAY)
    )
    WHERE id = {}
""".format(diary_id, diary_id, diary_id, diary_id, diary_id)

print("Updating started and ended fields for diary {}".format(
    diary_id
))
cursor.execute(sql)
connection.commit()

for d in deviceDict:
    for f in fieldDict:
        print("f value is {}".format(f))
        field_id = fieldDict[f].get('id')
        device_id = deviceDict[d]
        selargs = (device_id, field_id, datestamp, datestamp)
        print("selargs content is {}".format(selargs))
        cursor.execute(
            """
            select
                IFNULL(avg(z.value), 0) as avgval,
                IFNULL(min(z.value), 0) as minval,
                IFNULL(max(z.value), 0) as maxval
            from data z
            where z.device_id = %s
            and z.field_id  = %s
            and z.date >= %s && z.date < (%s + INTERVAL 1 DAY)
            and z.value > 0
            """,
            selargs
        )
        counters = cursor.fetchone()
        saveargs = (diary_id, device_id, field_id) + counters
        print("saveargs content is {}".format(saveargs))
        sql = """
            INSERT INTO diary_data(
                diary_id, device_id, field_id, avgval, minval, maxval
            )
            VALUES(
                %s, %s, %s, %s, %s, %s
            )
        """
        cursor.execute(sql, saveargs)

connection.commit()
cursor.close()
