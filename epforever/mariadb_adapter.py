from epforever.adapter import Adapter
import MySQLdb
from ast import literal_eval


class MariaDBAdapter(Adapter):
    cursor: None
    connection: None
    deviceDict: None
    fieldDict: None
    dashboardDict: None

    def __init__(self, config: dict):
        super().__init__(config)

        self.cursor = None
        self.connection = None
        self.deviceDict = None
        self.fieldDict = None
        self.dashboardDict = None

    def loadConfig(self):
        self.deviceDict = dict()
        self.fieldDict = dict()
        self.dashboardDict = dict()

        self.init()

        self.cursor.execute('SELECT id, name, port FROM device')
        devices = self.cursor.fetchall()
        for device in devices:
            self.devices.append({
                'id': device[0],
                'name': device[1],
                'port': device[2]
            })
            self.deviceDict[device[1]] = device[0]

        self.cursor.execute('''
            SELECT id, label, name, category, registeraddr FROM field
        ''')
        fields = self.cursor.fetchall()
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

        self.cursor.execute(
            'SELECT DISTINCT identifier, field_id FROM dashboard'
        )
        items = self.cursor.fetchall()
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
        self.cursor = self.connection.cursor()

        return True

    def saveRecord(self, record: dict, off: bool = False):
        querydata = []

        # TODO: get diary_id (from record[0].get('datestamp'))
        diary_id = self.__getDiaryId(record[0].get('datestamp'))
        if not off:
            # TODO: if diary_id is None:
            # Create a diary entry for this datestamp
            if diary_id is None:
                diary_id = self.__createDiary(record[0].get('datestamp'))

            print("saving ...")
            self.isoff = False
        else:
            print("saving (all devices are off) ...")
            if not self.isoff:
                print("saving last empty record ...")
                self.__addEmptyRecord()
                # TODO: Save counters of previous day in diary table
                self.__saveDiaryData(diary_id)
                self.isoff = True

        for r in record:
            device_id = self.deviceDict[r.get('device')]
            datestamp = "{} {}".format(r.get('datestamp'), r.get('timestamp'))
            for data in r.get('data'):
                field_id = self.fieldDict[data.get('field')]
                value = data.get('value')
                querydata.append((device_id, field_id, datestamp, value))
                if field_id in self.dashboardDict:
                    self.cursor.execute(
                        self._get_update_dashboard_sql(),
                        (
                            value,
                            self.dashboardDict[field_id],
                            field_id,
                            device_id
                        )
                    )

        if not off:
            self.cursor.executemany(
                self._get_saverecord_sql(),
                querydata
            )

        self.connection.commit()

    def __getDiaryId(self, datestamp):
        sql = "SELECT id FROM diary where datestamp = '{}'".format(datestamp)
        self.cursor.execute(sql)
        diary = self.cursor.fetchone()
        if diary is None:
            return None

        return diary[0]

    def __createDiary(self, datestamp):
        self.cursor.execute("INSERT INTO diary(datestamp) VALUES({})".format(
            datestamp
        ))
        return self.cursor.lastrowid

    def __saveDiaryData(self, diary_id):
        print('requested to save diary data from db')
        pass

    def __addEmptyRecord(self):
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

    def _get_empty_saverecord_sql(self):
        return """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(%s, %s, NOW(), %s)
            """
