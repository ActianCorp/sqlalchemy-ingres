# ingres/pyodbc.py
# Copyright 2020 Actian Corporation
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
"""
Ingres DB connector for the pyodbc/pypyodbc module
"""
from ingres_sa_dialect.base import IngresDialect
from sqlalchemy.engine.default import DefaultExecutionContext

class Ingres_pyodbc(IngresDialect):
    driver = 'pyodbc'

    def __init__(self, **kwargs):
        IngresDialect.__init__(self, **kwargs)

    @classmethod
    def dbapi(cls):
        return __import__('pyodbc')  # FIXME also test pypyodbc

    def create_connect_args(self, url):
        opts = url.translate_connect_args(username='uid', password='pwd', host='vnode')
        driver_name = 'Ingres'  # FIXME should have a connection option for this

        conn_list = []
        conn_list.append('Driver={' + driver_name + '}')  # FIXME using concat for now
        conn_list.append('Database=' + url.database)
        if not url.host:
            conn_list.append('Server=(local)')
        else:
            conn_list.append('Server=' + url.host)  # FIXME assumes a vnode - support HostName+ListenAddress and/or @ and port support.
            # FIXME port - str(url.port)
            
        if url.username:
            conn_list.append('UID=' + url.username)
        if url.password:
            conn_list.append('PWD=' + url.password)

        connection_str = ';'.join(conn_list)

        opts = {}
        opts.update(url.query)

        return ([connection_str], opts)


# FIXME push into base
class IngresExecutionContext(DefaultExecutionContext):
    def __init__(self, **kwargs):
        DefaultExecutionContext.__init__(self, **kwargs)

    def create_cursor(self):
        return self._connection.connection.cursor()

dialect = Ingres_pyodbc
