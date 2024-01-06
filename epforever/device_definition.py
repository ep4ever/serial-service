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
    FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS = (5, 6, 7, 8)
    PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'  # noqa: E501
    STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO = (1, 1.5, 2)

    def __init__(
        self,
        id: int,
        name: str,
        port: str,
        baudrate: int = 9600,
        always_on: bool = False
    ):
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
        self.baudrate = baudrate
        self.always_on = always_on
        self.bytesize = DeviceDefinition.EIGHTBITS
        self.parity = DeviceDefinition.PARITY_NONE
        self.stopbits = DeviceDefinition.STOPBITS_ONE

    def get_definition(self) -> Dict[str, Union[int, str]]:
        """
        :return: A dictionary containing the device definition's
        id, name and port.
        :rtype: Dict[str, Union[int, str]]
        """
        return {
            'id': self.id,
            'name': self.name,
            'port': self.port,
            'baudrate': self.baudrate,
            'bytesize': self.bytesize,
            'parity': self.parity,
            'stopbits': self.stopbits
        }
