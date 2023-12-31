from datetime import datetime
from io import TextIOWrapper
import json
import os
import tempfile
import time
from typing import List, cast

from tinydb import TinyDB

from epforever.adapter import Adapter
from epforever.device_instrument import DeviceInstrument
from epforever.register import Register
from epforever.registers import epever


class TinyDBAdapter(Adapter):

    def __init__(self, config: dict):
        super().__init__(config=config)

        self.db_name: str = ""
        self.nightenv_filepath: str = ""
        self.main_config: dict = {}

    def init(self) -> bool:
        self.main_config = self._get_main_config()
        if self.main_config is None:
            return False

        db_directory = self._get_db_directory()
        if db_directory is None:
            return False

        self.nightenv_filepath = os.path.join(
            tempfile.gettempdir(),
            '.nightenv'
        )
        if not self._nightenv_ready():
            return False

        self._init_database(db_directory)

        registers: List[Register] = self._load_registers()
        self.devices = self._load_devices(register_list=registers)

        return True

    def save_record(self, records: dict):
        if self.db_name != datetime.today().strftime("%Y-%m-%d") + ".json":
            self._init_database(
                db_directory=str(self.main_config.get('db_folder'))
            )

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
        print("saving offline record ...")
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

    def _init_database(self, db_directory: str):
        self.db_name = datetime.today().strftime("%Y-%m-%d") + ".json"
        db_path = os.path.join(db_directory, self.db_name)
        self.db = TinyDB(db_path)

    def _get_db_directory(self) -> str:
        db_directory: str = str(self.main_config.get('db_folder'))
        if not os.path.isdir(db_directory):
            print("ERROR: could not find the db_folder check config.yaml")
            return None

        return db_directory

    def _nightenv_ready(self) -> bool:
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

    def _get_main_config(self) -> dict:
        main_config: str = str(self.config.get('MAIN_CONFIG_PATH'))
        if not os.path.isfile(main_config):
            print(
                "ERROR: could not found config.json from path {}".format(
                    main_config
                )
            )
            return None

        f: TextIOWrapper = open(main_config)
        main_json_config: dict = json.load(f)
        f.close()

        return main_json_config

    def _load_registers(self) -> List[Register]:
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

        return registers

    def _load_devices(
        self,
        register_list: List[Register]
    ) -> List[DeviceInstrument]:
        devices: list = cast(list, self.main_config.get('devices'))
        count = 0
        device_list: List[DeviceInstrument] = []
        for device in devices:
            count += 1
            inst = DeviceInstrument(
                id=count,
                name=device.get('name'),
                port=device.get('port'),
            )
            inst.registers = register_list
            device_list.append(inst)

        return device_list
