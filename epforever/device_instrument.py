from ast import literal_eval
import logging
from serial import Serial, SerialException
from minimalmodbus import Instrument
from typing import List, cast
from device_definition import DeviceDefinition
from register import Register


class DeviceInstrument(DeviceDefinition):
    """
    A device object representing a connected instrument
    with its configuration, registers and status.

    :ivar registers: A list of registers associated with this device.
      :type registers: List[Register]

    :ivar instrument: An instance of minimalmodbus.Instrument
    representing the connected instrument.
      :type instrument: minimalmodbus.Instrument
      :default: None

    :ivar has_error: A boolean indicating if an error
    occurred during communication.
      :type has_error: bool
      :default: False

    :ivar is_off: A boolean indicating if the instrument is powered on.
      :type is_off: bool
      :default: False

    """
    REG_SIMPLE = "simple"
    REG_LOWHIGH = "lowhigh"

    def __init__(
        self,
        id: int,
        name: str,
        port: str,
        baudrate: int,
        always_on: int,
        liveness_field_name: str = '',
        registers: List[Register] = []
    ):
        """
        Initialize a new device with the given parameters and registers.
        """

        self.registers: List[Register] = registers
        super().__init__(id, name, port, baudrate, always_on)

        logging.debug(f"Initializing device {name} on port {port}")
        self.registers = registers
        self.instrument = self.__load_instrument()
        self.has_error = False
        self.is_off = False
        self.liveness_field_name = liveness_field_name

    def get_register_by_name(self, name: str) -> Register | None:
        """
        Return the register with the given name if
        it exists in this device's list of registers
        """
        for register in self.registers:
            if register.fieldname == name:
                return register

        return None

    def measure(self, measurement: dict):
        """
        Measure the value of a register on the device and
        add it to measurement.data.
        """
        self.has_error = False
        self.is_off = self.__check_is_off()

        if self.is_off:
            logging.warn(f"Device {self.name} is off!")

        for register in self.registers:
            serialvalue: float = 0.0
            try:
                if not self.is_off:
                    # take everything
                    serialvalue = self.__get_serial_value(register=register)
                elif register.type == 'counter':
                    # take only counter type field
                    serialvalue = self.__get_serial_value(register=register)
                else:
                    # just put a debug message to trace state counter skipped
                    logging.debug(
                        f"{register.fieldname} is a 'state' register and the device is off. returning zero"  # noqa E505
                    )
            except Exception as e:
                self.has_error = True
                logging.warn(
                    f"Could not retrieve value for {register.fieldname} on device {self.name}"  # noqa E505
                )
                logging.error(f"Error: {e}")

            datas: list = cast(list, measurement.get("data"))
            datas.append({
                "field": register.fieldname,
                "value": "{:.2f}".format(serialvalue)
            })

    def __load_instrument(self) -> Instrument:
        """
        Load the instrument with the given parameters and
        return it.
        """
        try:
            instrument = Instrument(
                port=self.port,
                slaveaddress=1,
                close_port_after_each_call=False,
            )
            s: Serial = cast(Serial, instrument.serial)
            s.baudrate = self.baudrate
            # default is 0.05 s
            s.timeout = 0.5

        except SerialException as e:
            logging.warn("Device: {} connection error: {}".format(
                self,
                e
            ))
            raise Exception("could not load device with err: {}".format(e))

        return instrument

    def __check_is_off(self):
        """
        Check if the device is powered on or not and
        return true if it is off.
        """
        if self.always_on:
            return False

        name = self.liveness_field_name
        register: Register = self.get_register_by_name(name)
        if register is None:
            raise RuntimeError(
                f"__check_is_off: register {name} could not be found"
            )

        try:
            value = self.instrument.read_register(
                literal_eval(register.value), 2, 4
            )
            return (value < 0.01)
        except Exception as e:
            logging.warn("has_power::Error on device {}. Error: {}".format(
                self.name,
                e
            ))
            # is off
            return True

    def __get_serial_value(self, register: Register) -> float:
        """
        Return the value of a register on the device as float.
        """
        serialvalue: float = 0.0
        if register.kind == DeviceInstrument.REG_SIMPLE:
            if register.datatype == 'LONG':
                serialvalue = self.instrument.read_long(
                    registeraddress=literal_eval(register.value)
                )/register.divider
            else:
                serialvalue = self.instrument.read_register(
                    literal_eval(register.value), 2, 4
                )
        if register.kind == DeviceInstrument.REG_LOWHIGH:
            lsb = self.instrument.read_register(
                literal_eval(register.lsb), 2, 4
            )
            msb = int(self.instrument.read_register(
                literal_eval(register.msb), 2, 4
            ))
            serialvalue = lsb + (msb << 8)
        return serialvalue
