import sys

import mysql.connector

if sys.version_info < (3, 6):
    ModuleNotFoundError = ImportError
try:
    from fdwmarket.settings.prod import FDWDB
except ModuleNotFoundError:
    from fdwmarket.settings.test import FDWDB


class QueryFDW:
    def __init__(self, fdw_identity):
        self.username = fdw_identity

    def identity(self):
        sqldata = ("", "", 0)
        cnx = mysql.connector.connect(**FDWDB)
        cursor = cnx.cursor()
        query = "SELECT username, password, id FROM users WHERE username = %(username)s"
        cursor.execute(query, {'username': self.username})

        for (username, password, id) in cursor:
            sqldata = username, password, id

        cursor.close()
        cnx.close()

        return sqldata
