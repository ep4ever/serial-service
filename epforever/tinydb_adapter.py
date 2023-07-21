import os
import json
import tempfile
from datetime import datetime
from tinydb import TinyDB

from epforever.adapter import Adapter
from epforever.adapter_error import AdapterError
from epforever.registers import epever


class TinyDBAdapter(Adapter):
    envConfig: dict
    db_name: str
    nightenv_filepath: str

    def loadConfig(self):
        lconfig = self.config.get('MAIN_CONFIG_PATH')
        if not os.path.isfile(lconfig):
            raise AdapterError(
                "ERROR: could not found config.json from path {}".format(
                    lconfig
                )
            )

        f = open(lconfig)
        self.envConfig = json.load(f)
        for device in self.envConfig.get('devices'):
            self.devices.append({
                'id': 0,
                'name': device.get('name'),
                'port': device.get('port')
            })

        self.register = epever

        f.close()

        self.nightenv_filepath = os.path.join(
            tempfile.gettempdir(),
            '.nightenv'
        )

    def init(self):
        db_directory = self.envConfig.get('db_folder')
        if not os.path.isdir(db_directory):
            print("ERROR: could not find the db_folder check config.yaml")
            return False

        self.db_name = datetime.today().strftime("%Y-%m-%d") + ".json"
        db_path = os.path.join(db_directory, self.db_name)
        self.db = TinyDB(db_path)

        try:
            with open(self.nightenv_filepath, 'w'):
                pass
        except OSError:
            print(
                "WARNING: could not write to file path {}".format(
                    self.nightenv_filepath
                )
            )
            return False

        return True

    def saveRecord(self, record):
        if self.db_name != datetime.today().strftime("%Y-%m-%d") + ".json":
            self.init()

        self.db.insert_multiple(record)

    def saveOffSun(self, values):
        with open(self.nightenv_filepath, "w") as f:
            lines = []
            for batt_values in values:
                lines.append(
                    "{}={}\n".format(
                        batt_values.get('device'),
                        batt_values.get('value')
                    )
                )

            f.writelines(lines)
            f.close()
