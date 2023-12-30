from ast import literal_eval
from serial import Serial, SerialException
from minimalmodbus import Instrument

from typing import List, cast
from epforever.device_definition import DeviceDefinition
from epforever.register import Register


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

    :ivar has_power: A boolean indicating if the instrument is powered on.
      :type has_power: bool
      :default: False

    """

    def __init__(
        self,
        id: int,
        name: str,
        port: str,
        registers: List[Register] = []
    ):
        super().__init__(id, name, port)

        self.registers = registers
        self.instrument = self.__load_instrument()
        self.has_error = False
        self.has_power = False

    def get_register_by_name(self, name: str) -> Register:
        for register in self.registers:
            if register.fieldname == name:
                return register

        return None

    def fill(self, record: dict):
        self.has_error = False
        self.has_power = self.__check_power_state()
        if not self.has_power:
            print(f"Device {self.name} is off!")
        if self.has_power:
            # still input current comming from this device
            try:
                self.__fillrecord(record)
            except Exception as e:
                print("Error on device {}, error {}".format(
                    self.name,
                    e
                ))
                self.has_error = True
                self.__fillrecord(
                    record=record,
                    empty=True
                )
        else:
            try:
                self.__fillrecord(
                    record=record,
                    withcounter=False
                )
            except Exception as e:
                print("Error on device {}, error {}".format(
                    self.name,
                    e
                ))
                self.has_error = True
                self.__fillrecord(
                    record=record,
                    empty=True,
                    withcounter=False
                )

    def __fillrecord(
        self,
        record: dict,
        empty: bool = False,
        withcounter: bool = True
    ):
        for register in self.registers:
            serialvalue = None
            if empty:
                serialvalue = 0
            else:
                if not withcounter and register.type == 'counter':
                    continue

                if register.kind == 'simple':
                    serialvalue = self.instrument.read_register(
                        literal_eval(register.value), 2, 4
                    )
                if register.kind == 'lowhigh':
                    lsb = self.instrument.read_register(
                        literal_eval(register.lsb), 2, 4
                    )
                    msb = int(self.instrument.read_register(
                        literal_eval(register.msb), 2, 4
                    ))
                    serialvalue = lsb + (msb << 8)

            if serialvalue is not None:
                datas: list = cast(list, record.get("data"))
                datas.append({
                    "field": register.fieldname,
                    "value": "{:.2f}".format(serialvalue)
                })

    def __load_instrument(self) -> Instrument:
        try:
            instrument = Instrument(
                port=self.port,
                slaveaddress=1,
                close_port_after_each_call=False,
            )
            s: Serial = cast(Serial, instrument.serial)
            s.baudrate = 115200
            # default is 0.05 s
            s.timeout = 1.2
        except SerialException as e:
            print("Device: {} connection error: {}".format(
                self,
                e
            ))
            raise Exception("could not load device with err: {}".format(e))

        return instrument

    def __check_power_state(self):
        # discrete value for day / night always return zero
        # so if pv_array_input_current is zero
        # the device does not produce anymore
        name = "rated_current"
        register: Register = self.get_register_by_name(name)
        if register is None:
            raise RuntimeError(f"register {name} could not be found")

        try:
            value = self.instrument.read_register(
                literal_eval(register.value), 2, 4
            )
            return (value > 0.0)
        except Exception as e:
            print("has_power::Error on device {}. Error: {}".format(
                self.name,
                e
            ))
            return False
