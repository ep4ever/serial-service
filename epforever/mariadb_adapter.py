from epforever.adapter import Adapter
import MySQLdb


class MariaDBAdapter(Adapter):
    def loadConfig(self):
        config = {
            'dbuser': self.config.get('DB_USER'),
            'dbpwd': self.config.get('DB_PWD'),
            'dbhost': self.config.get('DB_HOST'),
            'dbname': self.config.get('DB_NAME'),
            'devices': [],
            'registers': {}
        }

        connection = MySQLdb.connect(
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PWD'),
            host=self.config.get('DB_HOST'),
            database=self.config.get('DB_NAME')
        )
        cursor = connection.cursor()
        cursor.execute('SELECT id, name, port FROM device')
        devices = cursor.fetchall()
        for device in devices:
            config.get('devices').append({
                'id': device[0],
                'name': device[1],
                'port': device[2]
            })

        cursor.execute('''
            SELECT id, label, name, category, registeraddr FROM field
        ''')
        fields = cursor.fetchall()
        register = config.get('registers')
        for field in fields:
            keyval = field[1]
            if field[3] == 'simple':
                register[keyval] = {
                    'id': field[0],
                    'kind': 'simple',
                    'value': field[4],
                    'fieldname': field[2]
                }
            else:
                data = tuple(field[4].split('|'))
                register[keyval] = {
                    'id': field[0],
                    'kind': 'lowhigh',
                    'lsb': data[0],
                    'msb': data[1],
                    'fieldname': field[2]
                }
        self.register = register

        cursor.close()
        connection.close()

    def init(self):
        pass
