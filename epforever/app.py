import sys
import threading
import time

from epforever.adapter import Adapter
from epforever.device import Device


class EpforEverApp():

    def __init__(self, adapter: Adapter):
        self.adapter: Adapter = adapter
        self.devices: list = list()
        self.p_index: int = 0
        self.proc_char: dict = {
            0: "-",
            1: "\\",
            2: "|",
            3: "/",
        }
        self.runnable: bool = False

        self.all_devices_off = False

        self.adapter.load_config()

        for deviceDef in self.adapter.devices:
            print("creating com from devices {}".format(deviceDef))
            try:
                comDevice = Device(deviceDef, self.adapter.register)
                self.devices.append(comDevice)
            except Exception as e:
                print("error {}".format(e))
                sys.exit(1)

        self.runnable = self.__canrun()

    def run(self):
        if not self.runnable:
            return

        threading.Timer(15.0, self.run).start()

        records: list = []
        nboff: int = 0

        # get timestamps
        localtime = time.localtime()
        timestamp = time.strftime("%H:%M:%S", localtime)
        datestamp = time.strftime("%Y-%m-%d", localtime)

        # for each device
        for device in self.devices:
            record = self.__getrecord(device.name, timestamp, datestamp)
            device.fill(record)
            records.append(record)
            if not device.has_power():
                nboff = nboff + 1

        alloff = nboff == len(self.devices)
        if not alloff:
            self.adapter.save_record(
                records=records,
                off=alloff
            )
            self.all_devices_off = False
        elif not self.all_devices_off:
            self.adapter.save_empty_record()
            self.all_devices_off = True
        else:
            self.adapter.save_offline_record(records=records)

        if (self.p_index > 3):
            self.p_index = 0

        print(f"{self.proc_char[self.p_index]}", end="")
        print("\r", end="")

        self.p_index += 1

    def __canrun(self) -> bool:
        if len(self.devices) == 0:
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

    def __getrecord(
        self,
        name: str,
        timestamp: str,
        datestamp: str
    ):
        return {
            "device": name,
            "timestamp": timestamp,
            "datestamp": datestamp,
            "data": []
        }
