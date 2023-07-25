import time
import sys
import threading
from serial.serialutil import SerialException
from minimalmodbus import Instrument
from epforever.adapter import Adapter


class EpforEverApp():
    adapter: Adapter
    instruments: list
    p_index: int
    proc_char: dict
    register: dict
    runnable: bool
    nightenv_filepath: str

    def __init__(self, adapter: Adapter):
        self.adapter = adapter
        self.instruments = []
        self.p_index = 0
        self.proc_char = {
            0: "-",
            1: "\\",
            2: "|",
            3: "/",
        }

        self.adapter.loadConfig()

        for device in self.adapter.devices:
            print("creating instrument from devices {}".format(device))
            instrument = self.__create_instrument(device)
            if instrument is not None:
                self.instruments.append(instrument)
        self.register = self.adapter.register
        self.runnable = self.__canrun()

    def run(self):
        if not self.runnable:
            return

        if (self.p_index > 3):
            self.p_index = 0

        threading.Timer(15.0, self.run).start()

        # get timestamps
        localtime = time.localtime()
        timestamp = time.strftime("%H:%M:%S", localtime)
        datestamp = time.strftime("%Y-%m-%d", localtime)

        offsun_records = []
        records = []
        devices_with_no_data = []

        # for each device (first iteration)
        for device in self.instruments:
            if self.__nopower(device):
                record = {
                    "device": device[0],
                    "timestamp": timestamp,
                    "datestamp": datestamp,
                    "data": []
                }
                try:
                    self.__fillOffSunRecord(record, device)
                except Exception as e:
                    print("Error on device {}, error {}".format(
                        device[0],
                        e
                    ))
                    self.__fillOffSunRecord(record, device, True)

                offsun_records.append(record)
                devices_with_no_data.append(device)
            else:
                # still input current comming from this device
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
                    devices_with_no_data.append(device)

        # end foreach device

        # if there is no data available for all devices
        if len(offsun_records) == len(self.instruments):
            print("saving off sun values...")
            # we are in night mode
            self.adapter.saveOffSun(offsun_records)
        else:
            # at least one of the device has data.
            # for each device without data or with com error
            # we add an empty record
            # so that all devices stays on the same timeline
            for device in devices_with_no_data:
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

        if len(records) > 0:
            print("doing db insertion...")
            self.adapter.saveRecord(records)
            self.p_index += 1

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

    def __fillOffSunRecord(
        self, record: dict,
        device: list,
        empty: bool = False
    ):
        for key, item in self.register.items():
            serialvalue = None

            if item.get('type') == 'counter':
                continue

            if empty:
                record.get("data").append({
                    "field": item.get('fieldname'),
                    "value": "0"
                })
                continue

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

    def __nopower(self, device: list) -> bool:
        # discrete value for day / night always return zero
        # so if pv_array_input_current is zero
        # the device does not produce anymore
        try:
            h = self.register.get('pv_array_input_current').get('value')
            value = device[1].read_register(h, 2, 4)
            return (value < 0.01)
        except Exception as e:
            print("__nopower::Error on device {}. Error: {}".format(
                device[0],
                e
            ))
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
            sys.exit(1)

        return [device.get('name'), instrument]

    def __canrun(self) -> bool:
        if len(self.instruments) == 0:
            print(
                "WARNING: No device configured. Edit the config.yaml file"
            )
            return False

        if not self.adapter.init():
            print(
                "WARNING: could not initialize adapter"
            )
            return False

        return True
