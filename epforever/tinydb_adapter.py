from datetime import datetime
from io import TextIOWrapper
import json
import os
import tempfile
import time
from typing import List, cast

from tinydb import TinyDB

from epforever.adapter import Adapter
from epforever.adapter_error import AdapterError
from epforever.device_instrument import DeviceInstrument
from epforever.register import Register
from epforever.registers import epever


class TinyDBAdapter(Adapter):
    db_name: str
    nightenv_filepath: str

    def load_config(self):
        lconfig: str = str(self.config.get('MAIN_CONFIG_PATH'))
        if not os.path.isfile(lconfig):
            raise AdapterError(
                "ERROR: could not found config.json from path {}".format(
                    lconfig
                )
            )

        f: TextIOWrapper = open(lconfig)
        self.envConfig: dict = json.load(f)
        devices: list = cast(list, self.envConfig.get('devices'))
        count = 0
        for device in devices:
            count += 1
            inst = DeviceInstrument(
                id=count,
                name=device.get('name'),
                port=device.get('port'),
            )
            self.devices.append(inst)

        count = 0
        registers: List[Register] = []
        for r in epever:
            counter = epever.get(r)
            kind = counter.get('kind')
            if kind == 'discrete':
                continue

            count += 1
            register = Register(
                id=count,
                fieldname=counter.get('fieldname'),
            )
            if kind == 'simple':
                register.set_definition(
                    kind='simple',
                    value=counter.get('value')
                )
            else:
                register.set_definition(
                    kind='lowhigh',
                    lsb=counter.get('lsb'),
                    msb=counter.get('msb')
                )

            registers.append(register)

        for a in self.devices:
            a.registers = registers

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

    def save_record(self, records: dict):
        if self.db_name != datetime.today().strftime("%Y-%m-%d") + ".json":
            self.init()

        print("saving ...")
        self.db.insert_multiple(records)

    def save_empty_record(self):
        print("saving last empty record ...")

        localtime = time.localtime()
        timestamp = time.strftime("%H:%M:%S", localtime)
        datestamp = time.strftime("%Y-%m-%d", localtime)
        records = []
        for device in self.devices:
            record = {
                "device": device.name,
                "timestamp": timestamp,
                "datestamp": datestamp,
                "data": []
            }
            for r in device.registers:
                datas: list = cast(list, record.get("data"))
                datas.append({
                    'fieldname': r.fieldname,
                    'value': 0
                })
                records.append(record)

        self.db.insert_multiple(records)

    def save_offline_record(self, records: list):
        with open(self.nightenv_filepath, "w") as f:
            lines = []
            for r in records:
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
