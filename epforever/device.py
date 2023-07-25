
from minimalmodbus import Instrument
from serial.serialutil import SerialException


class Device:
    id: int
    name: str
    port: str
    instrument: None
    register: dict
    device_has_error: bool = False
    device_has_power: bool = False

    def __init__(self, rawdevice: dict, register: dict):
        self.id = rawdevice.get('id')
        self.name = rawdevice.get('name')
        self.port = rawdevice.get('port')
        self.register = register

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
    ) -> str:
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
                    msb = self.instrument.read_register(item.get('msb'), 2, 4)
                    serialvalue = lsb + (msb << 8)

            if serialvalue is not None:
                record.get("data").append({
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
            self.instrument.serial.baudrate = 115200
            # default is 0.05 s
            self.instrument.serial.timeout = 1.2
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
            h = self.register.get('pv_array_input_current').get('value')
            value = self.instrument.read_register(h, 2, 4)
            return (value > 0)
        except Exception as e:
            print("has_power::Error on device {}. Error: {}".format(
                self.name,
                e
            ))
            return False
