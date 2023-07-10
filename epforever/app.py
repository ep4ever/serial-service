import os
import time
import threading
from datetime import datetime
from tinydb import TinyDB
from serial.serialutil import SerialException
from minimalmodbus import Instrument
from epforever.registers import epever


class EpforEverApp():
    config: dict
    instruments: list
    p_index: int
    proc_char: dict
    register: dict
    runnable: bool
    db_name: str
    is_night_mode: bool

    def __init__(self, config: dict):
        self.config = config
        self.instruments = []
        self.p_index = 0
        self.proc_char = {
            0: "-",
            1: "\\",
            2: "|",
            3: "/",
        }
        for device in config.get('devices'):
            print("creating instrument from devices {}".format(device))
            instrument = self.__create_instrument(device)
            if instrument is not None:
                self.instruments.append(instrument)
        self.register = epever
        self.runnable = self.__canrun()
        self.is_night_mode = False

    def run(self):
        if not self.runnable:
            return

        if (self.p_index > 3):
            self.p_index = 0

        threading.Timer(15.0, self.run).start()

        if self.db_name != datetime.today().strftime("%Y-%m-%d") + ".json":
            self.__init_db()

        # get timestamps
        localtime = time.localtime()
        timestamp = time.strftime("%H:%M:%S", localtime)
        datestamp = time.strftime("%Y-%m-%d", localtime)

        offsun_batt_values = []
        devices_with_out_data = []
        records = []

        # for each device (first iteration)
        for device in self.instruments:
            if self.__isnight(device):
                h = self.register.get('battery_rated_voltage').get('value')
                print(f"no data available on this device {device[0]}")

                serialvalue = None
                try:
                    serialvalue = device[1].read_register(h, 2, 4)
                except Exception as e:
                    # add a zero value (not taken into account on client side)
                    serialvalue = 0
                    print("Error reading voltage, device {}, error {}".format(
                        device[0],
                        e
                    ))

                offsun_batt_values.append({
                    "device": device[0],
                    "value": serialvalue
                })

                # save this device for later use
                devices_with_out_data.append(device)
            else:
                # still input current comming from the device
                record = {
                    "device": device[0],
                    "timestamp": timestamp,
                    "datestamp": datestamp,
                    "data": []
                }

                try:
                    self.__fillrecord(record, device)
                    records.append(record)
                except Exception as e:
                    print("Error on device {}, error {}".format(
                        device[0],
                        e
                    ))
                    devices_with_out_data.append(device)

        # end foreach device

        # if there is no data available for all devices
        if len(offsun_batt_values) == len(self.instruments):
            # we are in night mode
            self.__fillOffSunEnv(offsun_batt_values)
            if not self.is_night_mode:
                for device in devices_with_out_data:
                    record = {
                        "device": device[0],
                        "timestamp": timestamp,
                        "datestamp": datestamp,
                        "data": []
                    }
                    self.__fillrecord(record, device, True)
                    records.append(record)
        else:
            # at least one of the device has data.
            # for each device without data or with com error
            # we add an empty record
            # so that all devices stays on the same timeline
            self.is_night_mode = False
            for device in devices_with_out_data:
                record = {
                    "device": device[0],
                    "timestamp": timestamp,
                    "datestamp": datestamp,
                    "data": []
                }
                self.__fillrecord(record, device, True)
                records.append(record)

        print(f"{self.proc_char[self.p_index]}", end="")
        print("\r", end="")

        # remaining data if at least one of the devices ?
        if len(self.instruments) > len(offsun_batt_values):
            print("doing db insertion...")
            self.db.insert_multiple(records)
            self.p_index += 1
        elif not self.is_night_mode:
            # insert a last zero record
            print("doing last db insertion...")
            self.db.insert_multiple(records)
            self.p_index += 1
            self.is_night_mode = True

    def __fillrecord(
        self, record: dict,
        device: list,
        empty: bool = False
    ) -> str:
        for key, item in self.register.items():
            serialvalue = None
            if empty:
                serialvalue = 0
            else:
                if item.get('kind') == 'simple':
                    serialvalue = device[1].read_register(
                        item.get('value'), 2, 4
                    )
                if item.get('kind') == 'lowhigh':
                    lsb = device[1].read_register(item.get('lsb'), 2, 4)
                    msb = device[1].read_register(item.get('msb'), 2, 4)
                    serialvalue = lsb + (msb << 8)

            if serialvalue is not None:
                record.get("data").append({
                    "field": item.get('fieldname'),
                    "value": "{:.2f}".format(serialvalue)
                })

    def __isnight(self, device: list) -> bool:
        # discrete value for day / night always return zero
        # so if pv_array_input_current is zero
        # the device does not produce anymore
        try:
            h = self.register.get('pv_array_input_current').get('value')
            value = device[1].read_register(h, 2, 4)
            return (value < 0.01)
        except Exception as e:
            print("__isnight::Error on device {}. Error: {}".format(
                device[0],
                e
            ))
            return True

    def __init_db(self) -> bool:
        db_directory = self.config.get('db_folder')
        if not os.path.isdir(db_directory):
            print("ERROR: could not find the db_folder check config.yaml")
            return False

        self.db_name = datetime.today().strftime("%Y-%m-%d") + ".json"
        db_path = os.path.join(db_directory, self.db_name)
        self.db = TinyDB(db_path)
        return True

    def __create_instrument(self, device: dict):
        instrument = None
        try:
            instrument = Instrument(
                port=device.get('port'),
                slaveaddress=1,
                close_port_after_each_call=False,
            )
            instrument.serial.baudrate = 115200
            # default is 0.05 s
            instrument.serial.timeout = 1.2
        except SerialException as e:
            print("Device: {} connection error: {}".format(
                device,
                e
            ))
            exit(1)

        return [device.get('name'), instrument]

    def __canrun(self) -> bool:
        if len(self.instruments) == 0:
            print(
                "WARNING: No device configured. Edit the config.yaml file"
            )
            return False

        if not self.__init_db():
            print(
                "WARNING: Edit the config.yaml file, missing db_folder path"
            )
            return False

        nightenv_path = self.config.get('nightenv_file', None)
        try:
            with open(nightenv_path, 'w'):
                pass
        except OSError:
            print(
                "WARNING: config.yaml, missing 'nightenv_path' file path"
            )
            return False

        return True

    def __fillOffSunEnv(self, offsun_batt_values: list):
        nightenv_path = self.config.get('nightenv_filepath')

        with open(nightenv_path, "w") as f:
            lines = []
            for batt_values in offsun_batt_values:
                lines.append(
                    "{}={}\n".format(
                        batt_values.get('device'),
                        batt_values.get('value')
                    )
                )

            f.writelines(lines)
            f.close()
