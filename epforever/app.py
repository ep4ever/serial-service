import time
import sys
import threading
from epforever.adapter import Adapter
from epforever.device import Device


class EpforEverApp():
    adapter: Adapter
    devices: list
    p_index: int
    proc_char: dict
    runnable: bool
    nightenv_filepath: str

    def __init__(self, adapter: Adapter):
        self.adapter = adapter
        self.p_index = 0
        self.proc_char = {
            0: "-",
            1: "\\",
            2: "|",
            3: "/",
        }

        self.adapter.loadConfig()

        for deviceDef in self.adapter.devices:
            print("creating com from devices {}".format(deviceDef))
            try:
                comDevice = Device(deviceDef, self.adapter.register)
                self.devices.append(comDevice)
            except Exception:
                sys.exit(1)

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

        records = []
        nopower_count = 0

        # for each device
        for device in self.devices:
            record = self.__getrecord(device.name, timestamp, datestamp)
            device.fill(record)
            records.append(record)
            if not device.has_power():
                nopower_count = nopower_count + 1

        # if there is no data available for all devices
        if nopower_count == len(self.devices):
            print("saving off sun values...")
            # we are in night mode
            self.adapter.saveOffSun(records)
        else:
            print("doing db insertion...")
            self.adapter.saveRecord(records)
            self.p_index += 1

        print(f"{self.proc_char[self.p_index]}", end="")
        print("\r", end="")

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
