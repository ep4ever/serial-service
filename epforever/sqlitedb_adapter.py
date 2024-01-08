import sqlite3
from typing import Any

from mariadb_adapter import MariaDBAdapter


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

    def _get_last_diary_sql(self):
        return """
        SELECT
            id,
            strftime('%Y-%m-%d', datestamp)
        FROM diary
        WHERE diary.started_at is NULL
        AND diary.ended_at is NULL
        ORDER BY id DESC LIMIT 1
        """

    # TODO: check this one for sqlite!
    def _get_update_diary_sql(self):
        return """
        UPDATE diary SET started_at = (
            SELECT MIN(time(z.date)) FROM data AS z
            WHERE z.date >= datetime(?)
            AND z.date < datetime(?, '+1 day')
            AND z.field_id IN (SELECT id FROM field WHERE to_dashboard=0)
        ), ended_at = (
            SELECT MAX(time(z.date)) FROM data AS z
            WHERE z.date >= datetime(?)
            AND z.date < datetime(?, '+1 day')
            AND z.field_id IN (SELECT id FROM field WHERE to_dashboard=0)
        )
        WHERE id = ?
        """

    # TODO: check this one for sqlite!
    def _get_average_field_value(self):
        return """
        SELECT
            IFNULL(avg(z.value), 0) as avgval,
            IFNULL(min(z.value), 0) as minval,
            IFNULL(max(z.value), 0) as maxval
        FROM data z
        WHERE z.device_id = ?
        AND z.field_id  = ?
        AND DATE(z.date) = DATE(?)
        """

    def _get_diary_insert_data_sql(self):
        return """
        INSERT INTO diary_data(
            diary_id, device_id, field_id, avgval, minval, maxval
        )
        VALUES(
            ?, ?, ?, ?, ?, ?
        )
        """
