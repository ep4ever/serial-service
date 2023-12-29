from abc import ABC, abstractmethod


class Adapter(ABC):
    """
    Abstract base class for adapters that handle data storage
    and device management.
    """

    def __init__(self, config: dict):
        self.config: dict = config
        self.devices: list = []
        self.register: dict = {}

    @abstractmethod
    def load_config(self):
        """
        Abstract method to be overridden for loading configuration
        data from the source.
        """
        raise NotImplementedError(
            "Load_config method needs to be implemented."
        )

    @abstractmethod
    def init(self):
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
