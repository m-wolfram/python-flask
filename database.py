import sqlite3
from flask import g


class SQLite3DB:
    def __init__(self):
        self.app = None

    def init_app(self, app):
        if self.app is None:
            self.app = app
        else:
            raise ValueError("App is already initialized!")

    def connect_db(self):
        con = sqlite3.connect(self.app.config["DB_PATH"])
        con.row_factory = sqlite3.Row
        return con

    def get_db(self):
        if not hasattr(g, "db"):
            g.db = self.connect_db()
        return g.db

    def init_db(self):
        with self.app.app_context():
            db = self.get_db()
            with self.app.open_resource("database/schema.sql", "r") as sql_schema:
                db.executescript(sql_schema.read())
            db.commit()


sqlite3db = SQLite3DB()
