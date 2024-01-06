import logging
import threading
import time
from epforever.adapter import Adapter


class EpforEverApp():

    def __init__(self, adapter: Adapter):

        logging.debug("In EpforEverApp constructor...")
        self.adapter: Adapter = adapter
        self.runnable: bool = True
        self.all_devices_off: bool = True
        self.runnable: bool = self.adapter.init()
        self.runnable: bool = self.__canrun()
        self.off_counter: int = 0
        self.refresh_rate: float = 15.0      # 15 seconds
        self.diary_backup_delay: int = 1200  # 20 minuts
        self.auto_diary_backup: bool = bool(self.adapter.config.get(
            'AUTO_DIARY_BACKUP',
            1
        ))
        self.nb_devices_off = 0
        self.live_device_count: int = 0
        for device in self.adapter.devices:
            if not device.always_on:
                self.live_device_count += 1
        logging.debug(f"Number of device that are always on is {self.live_device_count}")  # noqa E505

    def run(self):
        if not self.runnable:
            logging.warn("Instance cannot be run. Missing configuration settings ?")  # noqa E505
            return

        threading.Timer(self.refresh_rate, self.run).start()

        records: list = []
        self.nb_devices_off = 0

        # get timestamps
        localtime = time.localtime()
        timestamp = time.strftime("%H:%M:%S", localtime)
        datestamp = time.strftime("%Y-%m-%d", localtime)
        logging.debug(f"Current time stamp value is {timestamp}")
        # get records from devices that are not always on
        records: list = self.__get_device_records(
            timestamp=timestamp,
            datestamp=datestamp,
            always_on=0
        )

        alloff = self.nb_devices_off == self.live_device_count
        if not alloff:
            self.adapter.save_record(records=records)
            self.all_devices_off = False
            self.off_counter = 0
        elif not self.all_devices_off:
            self.adapter.save_empty_record()
            self.all_devices_off = True
        else:
            self.adapter.save_offline_record(records=records)
            self.off_counter += self.refresh_rate

        # get records for device that are always on
        records: list = self.__get_device_records(
            timestamp=timestamp,
            datestamp=datestamp,
            always_on=1
        )
        self.adapter.save_record(records=records)

        if self.off_counter == self.diary_backup_delay and self.auto_diary_backup:  # noqa: E501
            self.adapter.run_diary_backup()

    def diary_backup(self):
        self.adapter.run_diary_backup()

    def __get_device_records(
        self,
        timestamp,
        datestamp,
        always_on
    ) -> list:
        records: list = []
        nboff: int = 0

        # for each device
        for device in self.adapter.devices:
            if device.always_on != always_on:
                continue

            measurement = {
                "device": device.name,
                "timestamp": timestamp,
                "datestamp": datestamp,
                "data": []
            }
            device.measure(measurement=measurement)
            records.append(measurement)
            nboff += int(device.is_off)

        if always_on == 0:
            self.nb_devices_off = nboff

        return records

    def __canrun(self) -> bool:
        if not self.runnable:
            return False

        if len(self.adapter.devices) == 0:
            logging.warn(
                "WARNING: No device configured. Edit the config.yaml file"
            )
            return False

        return True
