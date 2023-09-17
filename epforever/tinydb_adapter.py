from datetime import datetime
from io import TextIOWrapper
import json
import os
import tempfile
import time
from typing import cast

from tinydb import TinyDB

from epforever.adapter import Adapter
from epforever.adapter_error import AdapterError
from epforever.registers import epever


class TinyDBAdapter(Adapter):
    db_name: str
    nightenv_filepath: str

    def loadConfig(self):
        lconfig: str = str(self.config.get('MAIN_CONFIG_PATH'))
        if not os.path.isfile(lconfig):
            raise AdapterError(
                "ERROR: could not found config.json from path {}".format(
                    lconfig
                )
            )

        f: TextIOWrapper = open(lconfig)
        self.envConfig: dict = json.load(f)
        self.devices: list = cast(list, self.envConfig.get('devices'))
        for device in self.devices:
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
        db_directory: str = str(self.envConfig.get('db_folder'))
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

    def saveRecord(self, record: dict, off: bool = False):
        if not off:
            if self.db_name != datetime.today().strftime("%Y-%m-%d") + ".json":
                self.init()

            self.db.insert_multiple(record)
        else:
            if not self.isoff:
                print("saving last empty record ...")
                self.__addEmptyRecord()
                self.isoff = True

            with open(self.nightenv_filepath, "w") as f:
                lines = []
                for r in record:
                    device = r.get('device')
                    for data in r.get('data'):
                        field = data.get('field')
                        value = data.get('value')
                        if field is None or value is None or device is None:
                            continue

                        line = '_'.join([device, field])
                        lines.append("{}={}\n".format(line, value))

                f.writelines(lines)
                f.close()

    def __addEmptyRecord(self):
        localtime = time.localtime()
        timestamp = time.strftime("%H:%M:%S", localtime)
        datestamp = time.strftime("%Y-%m-%d", localtime)
        records = []
        for device in self.devices:
            record = {
                "device": device.get('name'),
                "timestamp": timestamp,
                "datestamp": datestamp,
                "data": []
            }
            for r in self.register:
                if r.get('fieldname') is None:
                    continue
                datas: list = cast(list, record.get("data"))
                datas.append({
                    'fieldname': r.get('fieldname'),
                    'value': 0
                })
                records.append(record)

        self.db.insert_multiple(records)
