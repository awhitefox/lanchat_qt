import sqlite3
from time import time
from threading import Lock


DB_PATH = 'lanchat.sqlite'
CREATE_CMD = """CREATE TABLE Message (
    Id      INTEGER PRIMARY KEY
                    UNIQUE
                    NOT NULL,
    Server  STRING  NOT NULL,
    Author  STRING  NOT NULL,
    Message STRING  NOT NULL,
    Time    INTEGER NOT NULL
);"""


class SQLHelper:
    def __init__(self):
        self.lock = Lock()
        self.closed = False
        self.con = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cur = self.con.cursor()

    def get_closed(self):
        return self.closed

    def load_history(self, server):
        with self.lock:
            return self.cur.execute("SELECT Author, Message, Time FROM Message "
                                    "WHERE Server=?", (server,)).fetchall()

    def add_message(self, server, author, message):
        with self.lock:
            self.cur.execute("INSERT INTO Message (Server, Author, Message, Time) "
                             "VALUES (?, ?, ?, ?)", (server, author, message, int(time())))

    def delete_older_than_and_commit(self, days):
        with self.lock:
            self.cur.execute("DELETE FROM Message WHERE ?-Time>?", (int(time()), 86400 * days))
            self.con.commit()

    def delete_from_server_and_commit(self, server):
        with self.lock:
            self.cur.execute("DELETE FROM Message WHERE Server=?", (server,))
            self.con.commit()

    def delete_all_and_commit(self):
        with self.lock:
            self.cur.execute(f"DELETE FROM Message")
            self.con.commit()

    def commit(self):
        with self.lock:
            self.con.commit()

    def close(self):
        with self.lock:
            self.con.close()
            self.closed = True
