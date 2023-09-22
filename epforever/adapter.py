from abc import ABC, abstractmethod


class Adapter(ABC):

    def __init__(self, config: dict):
        self.config: dict = config
        self.devices: list = []
        self.register: dict = {}
        self.isoff = True

    @abstractmethod
    def loadConfig(self):
        raise NotImplementedError("loadConfig method must be overrided")

    @abstractmethod
    def init(self):
        raise NotImplementedError("init method must be overrided")

    @abstractmethod
    def saveRecord(self, record: list, off: bool = False):
        raise NotImplementedError("saveRecord method must be overrided")
