import sqlite3

from epforever.mariadb_adapter import MariaDBAdapter


class SqliteDBAdapter(MariaDBAdapter):
    """
    override connection settings
    """
    def init(self):
        if self.connection is not None:
            return True

        dbpath = self.config.get('DB_PATH')
        self.connection = sqlite3.connect(dbpath, check_same_thread=False)
        self.cursor = self.connection.cursor()

        return True

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
