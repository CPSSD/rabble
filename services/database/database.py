import logging
import sqlite3


class DB:

    def __init__(self, filename):
        self.filename = filename
        self.cursor = None

    def _get_cursor(self):
        # Connections and cursors can't be shared between threads so they're
        # kept here for now.
        # TODO(CianLR): Work out how gRPC threading works and how to share
        # these objects properly.
        conn = sqlite3.connect(self.filename)
        return conn.cursor()

    def commit(self):
        if not self.cursor:
            return
        self.cursor.connection.commit()
        self.cursor.close()
        self.cursor = None

    def discard_cursor(self):
        if self.cursor is not None:
            self.cursor.close()
        self.cursor = None

    def execute(self, statement, *params, commit=True):
        if self.cursor is None:
            self.cursor = self._get_cursor()
        self.cursor.execute(statement, params)
        res = self.cursor.fetchall()
        if commit:
            self.commit()
        return res

    def execute_count(self, statement, *params):
        cursor = self._get_cursor()
        cursor.execute(statement, params)
        count = cursor.rowcount
        cursor.connection.commit()
        cursor.close()
        return count

    def execute_script(self, script):
        cursor = self._get_cursor()
        cursor.executescript(script)
        cursor.close()


def build_database(logger, schema_path, db_path):
    db = DB(db_path)
    try:
        f = open(schema_path)
        script = f.read()
        f.close()
    except FileNotFoundError:
        logger.error("Couldn't find schema file at: '{}'", schema_path)
        raise
    db.execute_script(script)
    return db
