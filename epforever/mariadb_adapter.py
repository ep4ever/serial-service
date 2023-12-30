import time
from typing import List, cast

import MySQLdb
from MySQLdb.connections import Connection

from epforever.adapter import Adapter
from epforever.device_instrument import DeviceInstrument
from epforever.register import Register


class MariaDBAdapter(Adapter):

    def __init__(self, config: dict):
        super().__init__(config)

        self.connection: Connection = None  # pyright: ignore
        self.deviceDict: dict = {}
        self.fieldDict: dict = {}
        self.dashboardDict: dict = {}
        self.isSavingDiaryData: bool = False

    def load_config(self):
        self.init()

        cursor = self.connection.cursor()

        self.devices = self.__build_device_list_from_db(
            cursor=cursor,
        )

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

    def save_record(self, records: list):
        querydata = []
        cursor = self.connection.cursor()

        print("saving ...")
        for r in records:
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
                self.__add_to_dashboard(
                    cursor=cursor,
                    device_id=device_id,
                    field_id=field_id,
                    value=value
                )

        cursor.executemany(
            self._get_saverecord_sql(),
            querydata
        )

        self.connection.commit()

    def save_empty_record(self):
        self.__add_empty_record()
        print("creating diary stamp for today...")
        datestamp = time.strftime("%Y-%m-%d", time.localtime())
        self.__sync_diary(datestamp)

    def save_offline_record(self, records: list):
        print("Saving offline records...")
        cursor = self.connection.cursor()
        for r in records:
            device_id = self.deviceDict[r.get('device')]
            datas: list = cast(list, r.get("data"))
            for data in datas:
                field_id = self.fieldDict[data.get('field')]
                value = data.get('value')
                self.__add_to_dashboard(
                    cursor=cursor,
                    device_id=device_id,
                    field_id=field_id,
                    value=value
                )

        self.connection.commit()

    def __build_device_list_from_db(
        self,
        cursor
    ) -> List[DeviceInstrument]:

        register_list: List[Register] = self.__build_register_list_from_db(
            cursor
        )

        device_list: List[DeviceInstrument] = []
        cursor.execute('SELECT id, name, port FROM device')
        devices = cursor.fetchall()
        for device in devices:
            inst = DeviceInstrument(
                id=device[0],
                name=device[1],
                port=device[2],
            )
            inst.registers = register_list
            device_list.append(inst)
            self.deviceDict[device[1]] = device[0]

        return device_list

    def __build_register_list_from_db(self, cursor) -> List[Register]:
        register_list: List[Register] = []
        cursor.execute('''
            SELECT id, label, name, category, registeraddr FROM field
        ''')
        fields = cursor.fetchall()

        for field in fields:
            register = Register(id=field[0], fieldname=field[2])
            if field[3] == 'simple':
                register.set_definition(
                    kind='simple',
                    value=field[4]
                )
            else:
                data = tuple(field[4].split('|'))
                register.set_definition(
                    kind='lowhigh',
                    lsb=data[0],
                    msb=data[1]
                )
            register_list.append(register)
            self.fieldDict[field[2]] = field[0]

        return register_list

    def __add_to_dashboard(self, cursor, device_id, field_id, value):
        if field_id not in self.dashboardDict:
            return

        cursor.execute(
            self._get_update_dashboard_sql(),
            (
                value,
                self.dashboardDict[field_id],
                field_id,
                device_id
            )
        )

    def __sync_diary(self, datestamp):
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

    def __add_empty_record(self):
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
