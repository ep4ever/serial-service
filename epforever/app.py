import threading
import time

from epforever.adapter import Adapter


class EpforEverApp():

    def __init__(self, adapter: Adapter):
        self.adapter: Adapter = adapter
        self.p_index: int = 0
        self.proc_char: tuple = ("-", "\\", "|", "/")
        self.runnable: bool = True
        self.all_devices_off: bool = False
        self.runnable = self.adapter.init()
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
        for device in self.adapter.devices:
            measurement = {
                "device": device.name,
                "timestamp": timestamp,
                "datestamp": datestamp,
                "data": []
            }
            device.measure(measurement=measurement)
            records.append(measurement)
            nboff += int(device.is_off)

        alloff = nboff == len(self.adapter.devices)
        if not alloff:
            self.adapter.save_record(records=records)
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
        if not self.runnable:
            return False

        if len(self.adapter.devices) == 0:
            print(
                "WARNING: No device configured. Edit the config.yaml file"
            )
            return False

        return True

    def diary_backup(self):
        self.adapter.run_diary_backup()
