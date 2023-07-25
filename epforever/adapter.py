from abc import ABC, abstractmethod


class Adapter(ABC):
    config: dict
    devices: list[dict]
    register: dict
    isoff: bool

    def __init__(self, config: dict):
        self.config = config
        self.devices = []
        self.isoff = True

    @abstractmethod
    def loadConfig(self):
        raise NotImplementedError("loadConfig method must be overrided")

    @abstractmethod
    def init(self):
        raise NotImplementedError("init method must be overrided")

    @abstractmethod
    def saveRecord(self, record: dict, off: bool = False):
        raise NotImplementedError("saveRecord method must be overrided")
