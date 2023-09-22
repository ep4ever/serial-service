from ast import literal_eval
from typing import cast

import MySQLdb
from MySQLdb.connections import Connection

from epforever.adapter import Adapter


class MariaDBAdapter(Adapter):

    def __init__(self, config: dict):
        super().__init__(config)

        self.connection: Connection = None  # pyright: ignore
        self.deviceDict: dict = {}
        self.fieldDict: dict = {}
        self.dashboardDict: dict = {}
        self.isSavingDiaryData: bool = False

    def loadConfig(self):
        self.init()

        cursor = self.connection.cursor()
        cursor.execute('SELECT id, name, port FROM device')
        devices = cursor.fetchall()
        for device in devices:
            self.devices.append({
                'id': device[0],
                'name': device[1],
                'port': device[2]
            })
            self.deviceDict[device[1]] = device[0]

        cursor.execute('''
            SELECT id, label, name, category, registeraddr FROM field
        ''')
        fields = cursor.fetchall()
        register = {}
        for field in fields:
            keyval = field[1]
            if field[3] == 'simple':
                register[keyval] = {
                    'id': field[0],
                    'kind': 'simple',
                    'value': literal_eval(field[4]),
                    'fieldname': field[2]
                }
            else:
                data = tuple(field[4].split('|'))
                register[keyval] = {
                    'id': field[0],
                    'kind': 'lowhigh',
                    'lsb': literal_eval(data[0]),
                    'msb': literal_eval(data[1]),
                    'fieldname': field[2]
                }
            self.fieldDict[field[2]] = field[0]

        self.register = register

        cursor.execute(
            'SELECT DISTINCT identifier, field_id FROM dashboard'
        )
        items = cursor.fetchall()
        for item in items:
            self.dashboardDict[item[1]] = item[0]

    def init(self):
        if self.connection is not None:
            return True

        self.connection = MySQLdb.connect(
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PWD'),
            host=self.config.get('DB_HOST'),
            database=self.config.get('DB_NAME')
        )

        return True

    def saveRecord(self, record: list, off: bool = False):
        querydata = []
        cursor = self.connection.cursor()

        if not off:
            print("saving ...")
            self.isoff = False
        else:
            print("saving (all devices are off) ...")
            if not self.isoff:
                print("saving last empty record ...")
                self.__addEmptyRecord()
                print("creating diary stamp for today...")
                self.__syncDiary(record[0].get('datestamp'))
                self.isoff = True

        for r in record:
            device_id = self.deviceDict[r.get('device')]
            datestamp = "{} {}".format(
                r.get('datestamp'),
                r.get('timestamp')
            )
            datas: list = cast(list, r.get("data"))
            for data in datas:
                field_id = self.fieldDict[data.get('field')]
                value = data.get('value')
                querydata.append((device_id, field_id, datestamp, value))
                if field_id in self.dashboardDict:
                    cursor.execute(
                        self._get_update_dashboard_sql(),
                        (
                            value,
                            self.dashboardDict[field_id],
                            field_id,
                            device_id
                        )
                    )

        if not off:
            cursor.executemany(
                self._get_saverecord_sql(),
                querydata
            )

        self.connection.commit()

    def __syncDiary(self, datestamp):
        sql = "SELECT id FROM diary where datestamp = '{}'".format(datestamp)
        cursor = self.connection.cursor()
        cursor.execute(sql)
        diary = cursor.fetchone()
        if diary is None:
            cursor.execute(
                "INSERT INTO diary(datestamp) VALUES('{}')".format(
                    datestamp
                )
            )
            self.connection.commit()

    def __addEmptyRecord(self):
        querydata = []

        for device in self.deviceDict:
            for field in self.fieldDict:
                device_id = self.deviceDict[device]
                field_id = self.fieldDict[field]
                querydata.append((device_id, field_id, 0))

        cursor = self.connection.cursor()
        cursor.executemany(
            self._get_empty_saverecord_sql(),
            querydata
        )
        self.connection.commit()

    def _get_update_dashboard_sql(self):
        return """
            UPDATE dashboard
            SET value = %s
            WHERE identifier = %s
            AND field_id = %s
            AND device_id = %s
        """

    def _get_saverecord_sql(self):
        return """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(%s, %s, %s, %s)
            """

    def _get_savediarydata_sql(self):
        return """
            INSERT INTO diary_data(
                diary_id, device_id, field_id, avgval, minval, maxval
            )
            VALUES(
                %s, %s, %s, %s, %s, %s
            )
            """

    def _get_empty_saverecord_sql(self):
        return """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(%s, %s, NOW(), %s)
            """
