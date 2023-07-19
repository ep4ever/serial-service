from abc import ABC, abstractmethod


class Adapter(ABC):
    config: dict
    devices: []
    register: dict

    def __init__(self, config: dict):
        self.config = config
        self.devices = []

    @abstractmethod
    def loadConfig(self):
        raise NotImplementedError("loadConfig method must be overrided")

    @abstractmethod
    def init(self):
        raise NotImplementedError("init method must be overrided")

    @abstractmethod
    def saveRecord(self, record):
        raise NotImplementedError("saveRecord method must be overrided")