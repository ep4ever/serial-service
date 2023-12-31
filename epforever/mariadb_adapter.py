import time
from typing import Any, List, cast

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
        self.cursor: Any = None
        self.isSavingDiaryData: bool = False

    def init(self) -> bool:
        if self.connection is not None:
            return True

        self.cursor = self._init_connection()

        self.devices = self.__build_device_list_from_db()

        self.cursor.execute(
            'SELECT DISTINCT identifier, field_id FROM dashboard'
        )
        rows = self.cursor.fetchall()
        for row in rows:
            (identifier, field_id) = row
            self.dashboardDict[field_id] = identifier

        return True

    def save_record(self, records: list):
        querydata = []

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
                    device_id=device_id,
                    field_id=field_id,
                    value=value
                )

        self.cursor.executemany(
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
        for r in records:
            device_id = self.deviceDict[r.get('device')]
            datas: list = cast(list, r.get("data"))
            for data in datas:
                field_id = self.fieldDict[data.get('field')]
                value = data.get('value')
                self.__add_to_dashboard(
                    device_id=device_id,
                    field_id=field_id,
                    value=value
                )

        self.connection.commit()

    def _init_connection(self) -> Any:
        self.connection = MySQLdb.connect(
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PWD'),
            host=self.config.get('DB_HOST'),
            database=self.config.get('DB_NAME')
        )
        return self.connection.cursor()

    def __build_device_list_from_db(self) -> List[DeviceInstrument]:

        register_list: List[Register] = self.__build_register_list_from_db()

        device_list: List[DeviceInstrument] = []
        self.cursor.execute('SELECT id, name, port FROM device')
        devices = self.cursor.fetchall()
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

    def __build_register_list_from_db(self) -> List[Register]:
        register_list: List[Register] = []
        self.cursor.execute('''
            SELECT id, name, category, registeraddr FROM field
        ''')
        rows = self.cursor.fetchall()

        for row in rows:
            (id, name, category, registeraddr) = row
            register = Register(id=id, fieldname=name)
            if category == DeviceInstrument.REG_SIMPLE:
                register.set_definition(
                    kind=DeviceInstrument.REG_SIMPLE,
                    value=registeraddr
                )
            else:
                data = tuple(registeraddr.split('|'))
                register.set_definition(
                    kind=DeviceInstrument.REG_LOWHIGH,
                    lsb=data[0],
                    msb=data[1]
                )
            register_list.append(register)
            self.fieldDict[name] = id

        return register_list

    def __add_to_dashboard(self, device_id, field_id, value):
        if field_id not in self.dashboardDict:
            return

        self.cursor.execute(
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
        self.cursor.execute(sql)
        diary = self.cursor.fetchone()
        if diary is None:
            self.cursor.execute(
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

        self.cursor.executemany(
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
