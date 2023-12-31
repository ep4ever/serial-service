import sqlite3
from typing import Any

from epforever.mariadb_adapter import MariaDBAdapter


class SqliteDBAdapter(MariaDBAdapter):

    """
    override connection initialization
    """
    def _init_connection(self) -> Any:
        self.connection: sqlite3.Connection = sqlite3.connect(
            database=str(self.config.get('DB_PATH')),
            check_same_thread=False
        )
        return self.connection.cursor()

    def _get_update_dashboard_sql(self):
        return """
            UPDATE dashboard
            SET value = ?
            WHERE identifier = ?
            AND field_id = ?
            AND device_id = ?
        """

    def _get_saverecord_sql(self):
        return """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(?, ?, ?, ?)
            """

    def _get_empty_saverecord_sql(self):
        return """
            INSERT INTO data(device_id, field_id, date, value)
            VALUES(?, ?, datetime('now', 'localtime'), ?)
            """
