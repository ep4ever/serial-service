from abc import ABC, abstractmethod
import logging
from typing import List
from epforever.device_instrument import DeviceInstrument


class Adapter(ABC):
    """
    Abstract base class for adapters that handle data storage
    and device management.
    """

    def __init__(self, config: dict):

        logging.debug('In Adapter base class constructor...')
        self.config: dict = config
        self.devices: List[DeviceInstrument] = []
        self.register: dict = {}

    def get_device_by_name(self, name: str) -> DeviceInstrument | None:
        for device in self.devices:
            if device.name == name:
                return device

        return None

    @abstractmethod
    def init(self) -> bool:
        """
        Abstract method to be overriden for initializing connections
        or file handlers, as well as device list and register handling.
        """
        raise NotImplementedError("Init method needs to be implemented.")

    @abstractmethod
    def save_record(self, records: list):
        """
        Abstract method to be overridden for saving device state records
        and handling data persistence.
        """
        raise NotImplementedError(
            "Save_record method needs to be implemented."
        )

    @abstractmethod
    def save_empty_record(self):
        """
        Abstract method to be overridden for allowing the consumer
        of this object to add an empty record when needed.
        """
        raise NotImplementedError(
            "Save_empty_record method needs to be implemented."
        )

    @abstractmethod
    def save_offline_record(self, records: list):
        """
        Abstract method to be overridden for saving device state records
        and handling data persistence when devices are off.
        """
        raise NotImplementedError(
            "save_offline_record method needs to be implemented."
        )

    @abstractmethod
    def run_diary_backup(self):
        """
        Abstract method to be overridden for saving daily stats.
        """
        raise NotImplementedError(
            "diary_backup method needs to be implemented."
        )
