from epforever.adapter import Adapter
import MySQLdb
from ast import literal_eval


class MariaDBAdapter(Adapter):
    cursor: None
    connection: None
    deviceDict: None
    fieldDict: None

    def loadConfig(self):
        self.deviceDict = dict()
        self.fieldDict = dict()

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

    def saveRecord(self, record):
        querydata = []
        for r in record:
            device_id = self.deviceDict[r.get('device')]
            datestamp = "{} {}".format(r.get('datestamp'), r.get('timestamp'))
            for data in r.get('data'):
                field_id = self.fieldDict[data.get('field')]
                value = data.get('value')
                querydata.append((device_id, field_id, datestamp, value))

        self.cursor.executemany(
            "INSERT INTO data(device_id, field_id, date, value) VALUES(%s, %s, %s, %s)",  # noqa: E501
            querydata
        )
        self.connection.commit()
