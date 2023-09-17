from typing import cast

from serial import Serial
from serial.serialutil import SerialException

from minimalmodbus import Instrument


class Device:

    def __init__(self, rawdevice: dict, register: dict):
        self.instrument: Instrument
        self.id: int = int(str(rawdevice.get('id')))
        self.name: str = str(rawdevice.get('name'))
        self.port: str = str(rawdevice.get('port'))
        self.register: dict = register
        self.device_has_error: bool = False
        self.device_has_power: bool = False

        self.__loadInstrument()

    def has_error(self):
        return self.device_has_error

    def has_power(self):
        return self.device_has_power

    def fill(self, record: dict):
        self.device_has_error = False
        self.device_has_power = self.__has_power()

        if self.device_has_power:
            # still input current comming from this device
            try:
                self.__fillrecord(record)
            except Exception as e:
                print("Error on device {}, error {}".format(
                    self.name,
                    e
                ))
                self.device_has_error = True
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
                self.device_has_error = True
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
        for key, item in self.register.items():
            serialvalue = None
            if empty:
                serialvalue = 0
            else:
                if not withcounter and item.get('type') == 'counter':
                    continue

                if item.get('kind') == 'simple':
                    serialvalue = self.instrument.read_register(
                        item.get('value'), 2, 4
                    )
                if item.get('kind') == 'lowhigh':
                    lsb = self.instrument.read_register(item.get('lsb'), 2, 4)
                    msb = int(self.instrument.read_register(
                        item.get('msb'), 2, 4
                    ))
                    serialvalue = lsb + (msb << 8)

            if serialvalue is not None:
                datas: list = cast(list, record.get("data"))
                datas.append({
                    "field": item.get('fieldname'),
                    "value": "{:.2f}".format(serialvalue)
                })

    def __loadInstrument(self):
        try:
            self.instrument = Instrument(
                port=self.port,
                slaveaddress=1,
                close_port_after_each_call=False,
            )
            s: Serial = cast(Serial, self.instrument.serial)
            s.baudrate = 115200
            # default is 0.05 s
            s.timeout = 1.2
        except SerialException as e:
            print("Device: {} connection error: {}".format(
                self,
                e
            ))
            raise Exception("could not load device with err: {}".format(e))

    def __has_power(self):
        # discrete value for day / night always return zero
        # so if pv_array_input_current is zero
        # the device does not produce anymore
        try:
            input_current: dict = cast(
                dict,
                self.register.get('pv_array_input_current')
            )
            h: int = cast(int, input_current.get('value'))
            value = self.instrument.read_register(h, 2, 4)
            return (value > 0)
        except Exception as e:
            print("has_power::Error on device {}. Error: {}".format(
                self.name,
                e
            ))
            return False
