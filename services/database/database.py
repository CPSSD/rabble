import logging
import sqlite3

class DB:
    def __init__(self, filename):
        self.filename = filename

    def _get_cursor(self):
        # Connections and cursors can't be shared between threads so they're
        # kept here for now.
        # TODO(CianLR): Work out how gRPC threading works and how to share
        # these objects properly.
        conn = sqlite3.connect(self.filename)
        return conn.cursor()

    def execute(self, statement, *params):
        cursor = self._get_cursor()
        cursor.execute(statement, params)
        res = cursor.fetchall()
        cursor.close()
        return res

    def execute_script(self, script):
        cursor = self._get_cursor()
        cursor.executescript(script)
        cursor.close()

def build_database(logger, schema_path, db_path='rabble.db'):
    db = DB(db_path)
    try:
        script = open(schema_path).read()
    except FileNotFoundError:
        logger.error("Couldn't find schema file at: '{}'", schema_path)
        raise
    db.execute_script(script)
    return db

