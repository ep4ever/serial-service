import logging
from typing import Any, List, cast
import MySQLdb
from MySQLdb.connections import Connection

from adapter import Adapter
from device_instrument import DeviceInstrument
from register import Register

"""
MariaDBAdapter class for managing data communication with the MariaDB database.

:param config: A dictionary containing configuration information
for connecting to and interacting with the MariaDB database.

Attributes:
   connection (Connection): The MariaDB connection object.
   dashboardDict (dict): A dictionary used to store dashboard data.
   cursor (Any): The MariaDB cursor object used
   for executing queries and fetching results.
"""


class MariaDBAdapter(Adapter):

    def __init__(self, config: dict):
        super().__init__(config)
        logging.debug('In MariaDBAdapter constructor...')
        self.connection: Connection = None  # pyright: ignore
        self.dashboardDict: dict = {}
        self.cursor: Any = None

    def init(self) -> bool:
        """
       Initializes the Adapter object by connecting to the database,
       fetching essential data.
       :return: True if initialization was successful, False otherwise.
       """
        if self.connection is not None:
            logging.warn("connection instance has already been initialized")  # noqa E505
            return True

        self.cursor = self._init_connection()

        self.devices = self.__build_device_list_from_db()

        logging.debug("Creating dashboard dictionary...")
        self.cursor.execute(
            """
            SELECT DISTINCT identifier, field_id
            FROM dashboard
            WHERE field_id IS NOT NULL
            """
        )
        rows = self.cursor.fetchall()
        for row in rows:
            (identifier, field_id) = row
            self.dashboardDict[field_id] = identifier

        return True

    def save_record(self, records: list):
        """
        Saves the provided records to the database
        :param records: A list of Record objects containing
        device information, timestamp, and data.
        """
        querydata = []
        scope: str = ''
        for r in records:
            device = self.get_device_by_name(r.get('device'))
            curr_scope = 'always on devices' if device.always_on else 'live devices'  # noqa E505
            if scope == '':
                scope = curr_scope
            elif scope != curr_scope:
                logging.warn(
                    "save_record should not be called with mixed devices type"
                )
            datestamp = "{} {}".format(
                r.get('datestamp'),
                r.get('timestamp')
            )
            datas: list = cast(list, r.get("data"))

            for data in datas:
                field = device.get_register_by_name(data.get('field'))
                value = data.get('value')
                querydata.append((device.id, field.id, datestamp, value))
                self.__add_to_dashboard(
                    device_id=device.id,
                    field_id=field.id,
                    value=value
                )

        if len(querydata) > 0:
            logging.info(f"saving {scope}...")
            self.cursor.executemany(
                self._get_saverecord_sql(),
                querydata
            )
            self.connection.commit()

    def save_empty_record(self):
        """
        Saves an empty record to the database
        """
        querydata = []

        for device in self.devices:
            if device.always_on == 1:
                # do not save empty data to an always on device
                continue

            for field in device.registers:
                if field.type == 'counter':
                    # do not save empty record on a counter
                    continue
                querydata.append((device.id, field.id, 0))

        if len(querydata) > 0:
            logging.debug("saving empty record...")
            self.cursor.executemany(
                self._get_empty_saverecord_sql(),
                querydata
            )
            self.connection.commit()

    def save_offline_record(self, records: list):
        """
        Saves the provided offline records to the database
        if they are from devices that don't have always-on status.
        :param records: A list of Record objects containing
        device information, timestamp, and data.
        """
        querydata = []

        for r in records:
            device = self.get_device_by_name(r.get('device'))
            if device.always_on == 1:
                # do not save offline data from an always on device
                continue
            datas: list = cast(list, r.get("data"))
            datestamp = "{} {}".format(
                r.get('datestamp'),
                r.get('timestamp')
            )
            for data in datas:
                field = device.get_register_by_name(data.get('field'))
                value = data.get('value')
                self.__add_to_dashboard(
                    device_id=device.id,
                    field_id=field.id,
                    value=value
                )
                if field.type == 'counter':
                    # when offline we are only saving counter type fields
                    querydata.append((device.id, field.id, datestamp, value))

        if len(querydata) > 0:
            logging.info("Saving offline records...")
            self.cursor.executemany(
                self._get_saverecord_sql(),
                querydata
            )
            self.connection.commit()

    def sync_diary(self, datestamp):
        sql = "SELECT id FROM diary where datestamp = '{}'".format(datestamp)
        self.cursor.execute(sql)
        diary = self.cursor.fetchone()
        if diary is None:
            self.cursor.execute(
                "INSERT INTO diary(datestamp) VALUES('{}')".format(
                    datestamp
                )
            )
            self.connection.commit()

    def run_diary_backup(self):
        """
        Creates a new diary stamp and updates the started and ended fields
        for an existing diary in the database.
        It also calculates daily averages for all counter-type registers
        of non-always on devices, and inserts their data into the diary.
        """
        self.cursor.execute(self._get_last_diary_sql())
        diary_info = self.cursor.fetchone()
        if diary_info is None:
            logging.warn("latest diary backup already setup, skipping...")
            return

        (diary_id, datestamp) = diary_info
        logging.debug(f"Updating started and ended fields for diary number {diary_id}")  # noqa E505
        self.cursor.execute(
            self._get_update_diary_sql(),
            (datestamp, datestamp, datestamp, datestamp, diary_id)
        )
        self.connection.commit()

        for device in self.devices:
            # skip always on devices for the diary data
            if device.always_on:
                continue

            for field in device.registers:
                # do not save diary data on counter type fields
                if field.type == 'counter':
                    continue

                self.cursor.execute(
                    self._get_average_field_value(),
                    (device.id, field.id, datestamp)
                )

                counters = self.cursor.fetchone()
                saveargs = (diary_id, device.id, field.id) + counters
                self.cursor.execute(
                    self._get_diary_insert_data_sql(),
                    saveargs
                )
            logging.info(f"Device number {device.id} OK")

        self.connection.commit()
        logging.info("Diary backup succeeded!")

    def _init_connection(self) -> Any:
        logging.info("Initializing MySQLdb connection...")
        self.connection = MySQLdb.connect(
            user=self.config.get('DB_USER'),
            password=self.config.get('DB_PWD'),
            host=self.config.get('DB_HOST'),
            database=self.config.get('DB_NAME')
        )
        return self.connection.cursor()

    def __build_device_list_from_db(self) -> List[DeviceInstrument]:

        register_list: List[Register] = self.__build_register_list_from_db()
        logging.debug("Reading device list from database...")
        device_list: List[DeviceInstrument] = []
        self.cursor.execute("""
            SELECT
                dv.id,
                dv.name,
                dv.port,
                dv.baudrate,
                dv.register_id,
                dv.always_on,
                rg.ref_liveness_field_name
            FROM device AS dv
            JOIN register AS rg ON rg.id = dv.register_id
        """)
        devices = self.cursor.fetchall()
        for row in devices:
            (id, name, port, baudrate, register_id, always_on, liveness_field_name) = row  # noqa 505
            inst = DeviceInstrument(
                id=id,
                name=name,
                port=port,
                baudrate=baudrate,
                always_on=always_on,
                liveness_field_name=liveness_field_name
            )
            inst.registers = list(
                filter(lambda x: x.register_id == register_id, register_list)
            )
            device_list.append(inst)

        return device_list

    def __build_register_list_from_db(self) -> List[Register]:
        register_list: List[Register] = []
        logging.debug("Reading register list from the database...")
        self.cursor.execute("""
            SELECT
                id,
                name,
                category,
                registeraddr,
                to_dashboard,
                register_id,
                datatype,
                divider
            FROM field
        """)
        rows = self.cursor.fetchall()

        for row in rows:
            (id, name, category, registeraddr, to_dashboard, register_id, datatype, divider) = row  # noqa E501
            register = Register(
                id=id,
                fieldname=name,
                register_id=register_id,
                datatype=datatype,
                divider=divider
            )
            if category == DeviceInstrument.REG_SIMPLE:
                register.set_definition(
                    kind=DeviceInstrument.REG_SIMPLE,
                    value=registeraddr
                )
            else:
                (lsbval, msbval) = tuple(registeraddr.split('|'))
                register.set_definition(
                    kind=DeviceInstrument.REG_LOWHIGH,
                    lsb=lsbval,
                    msb=msbval
                )

            if to_dashboard:
                # force type of field to counter for consistency
                logging.debug(f"Register {register.fieldname} has been setted to type counter")  # noqa E505
                register.type = 'counter'

            register_list.append(register)

        return register_list

    def __add_to_dashboard(self, device_id, field_id, value):
        if field_id not in self.dashboardDict:
            return

        self.cursor.execute(
            self._get_update_dashboard_sql(),
            (
                value,
                self.dashboardDict[field_id],
                field_id,
                device_id
            )
        )

    def _get_update_dashboard_sql(self):
        return """
            UPDATE dashboard
            SET value = %s
            WHERE identifier = %s
            AND field_id = %s
            AND device_id = %s
        """

    def _get_saverecord_sql(self):
        return """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(%s, %s, %s, %s)
            """

    def _get_savediarydata_sql(self):
        return """
            INSERT INTO diary_data(
                diary_id, device_id, field_id, avgval, minval, maxval
            )
            VALUES(
                %s, %s, %s, %s, %s, %s
            )
            """

    def _get_empty_saverecord_sql(self):
        return """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(%s, %s, NOW(), %s)
            """

    def _get_update_diary_sql(self):
        return """
        UPDATE diary SET started_at = (
            SELECT MIN(time(z.date)) FROM data AS z
            WHERE z.date >= DATE(?)
            AND z.date < (DATE(?) + INTERVAL 1 DAY)
            AND z.field_id IN (SELECT id FROM field WHERE to_dashboard=0)
        ), ended_at = (
            SELECT MAX(time(z.date)) FROM data AS z
            WHERE z.date >= DATE(?)
            AND z.date < (DATE(?) + INTERVAL 1 DAY)
            AND z.field_id IN (SELECT id FROM field WHERE to_dashboard=0)
        )
        WHERE id = ?
        """

    def _get_average_field_value(self):
        return """
        select
            IFNULL(avg(z.value), 0) as avgval,
            IFNULL(min(z.value), 0) as minval,
            IFNULL(max(z.value), 0) as maxval
        from data z
        where z.device_id = %s
        and z.field_id  = %s
        and DATE(z.date) = %s
        """

    def _get_diary_insert_data_sql(self):
        return """
        INSERT INTO diary_data(
            diary_id, device_id, field_id, avgval, minval, maxval
        )
        VALUES(
            %s, %s, %s, %s, %s, %s
        )
        """

    def _get_last_diary_sql(self):
        return """
        SELECT
            id,
            DATE_FORMAT(datestamp, '%Y-%m-%d')
        FROM diary
        WHERE diary.started_at is NULL
        AND diary.ended_at is NULL
        ORDER BY id DESC LIMIT 1
        """
