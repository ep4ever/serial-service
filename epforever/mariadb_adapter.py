from epforever.adapter import Adapter
import MySQLdb
from ast import literal_eval


class MariaDBAdapter(Adapter):
    cursor: None
    connection: None
    deviceDict: None
    fieldDict: None
    dashboardDict: None
    offsun_mode: bool = False

    def loadConfig(self):
        self.deviceDict = dict()
        self.fieldDict = dict()
        self.dashboardDict = dict()

        cnx = MySQLdb.connect(
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PWD'),
            host=self.config.get('DB_HOST'),
            database=self.config.get('DB_NAME')
        )
        cursor = cnx.cursor()
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

        cursor.execute('SELECT DISTINCT identifier, field_id FROM dashboard')
        items = cursor.fetchall()
        for item in items:
            self.dashboardDict[item[1]] = item[0]

        cursor.close()
        cnx.close()

    def init(self):
        self.connection = MySQLdb.connect(
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PWD'),
            host=self.config.get('DB_HOST'),
            database=self.config.get('DB_NAME')
        )
        self.cursor = self.connection.cursor()

        return True

    def saveRecord(self, record, onlyDashBoard: bool = False):
        querydata = []

        # if onlyDashBoard (called from saveOffSun) and
        # offsun_mode flag is False
        if onlyDashBoard and not self.offsun_mode:
            self.__addEmptyRecord()
            self.offsun_mode = True

        if not onlyDashBoard:
            # call saveRecord has been made outside of this object (app)
            self.offsun_mode = False

        for r in record:
            device_id = self.deviceDict[r.get('device')]
            datestamp = "{} {}".format(r.get('datestamp'), r.get('timestamp'))
            for data in r.get('data'):
                field_id = self.fieldDict[data.get('field')]
                value = data.get('value')
                querydata.append((device_id, field_id, datestamp, value))
                if field_id in self.dashboardDict:
                    self.cursor.execute(
                        """
                        UPDATE dashboard
                        SET value = %s
                        WHERE identifier = %s
                        AND field_id = %s
                        AND device_id = %s
                        """,
                        (
                            value,
                            self.dashboardDict[field_id],
                            field_id,
                            device_id
                        )
                    )

        if not onlyDashBoard:
            self.cursor.executemany(
                """
                INSERT INTO data(device_id, field_id, date, value)
                VALUES(%s, %s, %s, %s)
                """,
                querydata
            )

        self.connection.commit()

    def saveOffSun(self, record):
        self.saveRecord(record, True)

    def __addEmptyRecord(self):
        querydata = []

        for device in self.deviceDict:
            for field in self.fieldDict:
                device_id = self.deviceDict[device]
                field_id = self.fieldDict[field]
                querydata.append((device_id, field_id, 0))

        self.cursor.executemany(
            """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(%s, %s, NOW(), %s)
            """,
            querydata
        )
        self.connection.commit()
