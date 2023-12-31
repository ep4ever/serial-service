import logging
import threading
import time
from adapter import Adapter


class EpforEverApp():
    """
    A class representing the EpforEverApp instance, responsible
    for interacting with Epifan devices and managing data collection.
    Initializes the EpforEverApp instance by initializing
    the Adapter object and registering
    callbacks to monitor the connected devices.

    :param adapter: An instance of Adapter.
    """

    def __init__(self, adapter: Adapter):
        """
       Initialize the EpforEverApp instance with an Adapter object.
       :param adapter: An instance of Adapter
       to interact with the devices.
       """
        logging.debug('In EpforEverApp constructor...')
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
        logging.info(
            f"Device not always on count is: {self.live_device_count}"
        )

    def run(self):
        """
        Start the EpforEverApp instance, collecting
        device data and saving records.
        If all devices are offline, a diary backup will be triggered after the
        specified delay.
        """
        if not self.runnable:
            logging.warn(
                'Instance cannot be run. Missing configuration settings ?'
            )
            return

        threading.Timer(self.refresh_rate, self.run).start()

        records: list = []

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
            # at least one live device is on so
            # live device that are off contains en
            # empty record to keep them in time sync
            self.adapter.save_record(records=records)
            self.all_devices_off = False
            # reset off counter diay backup to zero
            self.off_counter = 0
        elif not self.all_devices_off:
            # alloff flag is true so add an empty record
            # to live devices
            self.adapter.save_empty_record()
            # instance flag to prevent adding another empty
            # record on the next tick
            self.all_devices_off = True
            # create an empty diary entry if it does not exists
            logging.info("creating diary stamp for today...")
            self.adapter.sync_diary(datestamp)
        else:
            # save offline datas from live devices
            self.adapter.save_offline_record(records=records)
            # increment the off_counter flag
            # when this flag is equal to diary_backup_delay
            # the diary is filled with days data (cf. bellow)
            self.off_counter += self.refresh_rate

        # get records for device that are always on (running 24/24)
        records: list = self.__get_device_records(
            timestamp=timestamp,
            datestamp=datestamp,
            always_on=1
        )
        # and save them
        self.adapter.save_record(records=records)

        # if off counter is equal to diary backup delay
        # and if auto diary backup is defined to True
        # runs the diary packup method of the adapter
        if self.off_counter == self.diary_backup_delay and self.auto_diary_backup:  # noqa: E501
            self.adapter.run_diary_backup()

    def diary_backup(self):
        """
        Manually trigger a diary backup.
        """
        self.adapter.run_diary_backup()

    def __get_device_records(
        self,
        timestamp,
        datestamp,
        always_on
    ) -> list:
        """
        Collect device data and save records.

        :param timestamp: The current time format for the Epifan devices' logs.
        :param datestamp: The current date format for the Epifan devices' logs.
        :param always_on: A boolean value specifying whether to collect records
        from devices that are online.
        """
        records: list = []
        nboff: int = 0
        self.nb_devices_off = 0

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
        """
        Check the EpforEverApp instance's runnability status,
        returning True if all conditions are met.
        """
        if not self.runnable:
            return False

        if len(self.adapter.devices) == 0:
            logging.warn(
                "WARNING: No device configured. Edit the config.yaml file"
            )
            return False

        return True
