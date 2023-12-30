from typing import Dict, Union


class DeviceDefinition:
    """
    A Python class representing the definition of a device in a system.

    :ivar id: The unique identifier for this device.
    This value must be greater than zero.
    :type id: int

    :ivar name: The name of this device.
    This value must be at least six characters long.
    :type name: str

    :ivar port: The port to which the device is connected.
    This value must not be empty.
    :type port: str
    """

    id: int
    name: str
    port: str

    def __init__(self, id: int, name: str, port: str):
        if id <= 0:
            raise ValueError(
                "Device Definition's ID must be greater than zero."
            )
        elif len(name) < 6:
            raise ValueError(
                "Device Definition's name must be at least 6 characters long."
            )
        elif not port:
            raise ValueError("Device Definition's port must not be empty.")

        self.id = id
        self.name = name
        self.port = port

    def get_definition(self) -> Dict[str, Union[int, str]]:
        """
        :return: A dictionary containing the device definition's
        id, name and port.
        :rtype: Dict[str, Union[int, str]]
        """
        return {
            'id': self.id,
            'name': self.name,
            'port': self.port
        }
