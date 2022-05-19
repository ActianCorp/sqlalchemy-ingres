# ingres/pyodbc.py
# Copyright 2020 Actian Corporation
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
"""
Ingres DB connector for the pyodbc/pypyodbc module
"""

import os

from sqlalchemy.engine.default import DefaultExecutionContext

from ingres_sa_dialect.base import IngresDialect


try:
    ModuleNotFoundError  # Python 3 sanity check
except NameError:
    # Python 2.7
    ModuleNotFoundError = ImportError


class Ingres_pyodbc(IngresDialect):
    driver = 'pyodbc'
    supports_statement_cache = False  # quiesce https://sqlalche.me/e/14/cprf  NOTE `IngresDialect.supports_statement_cache` is not actually picked up by SA warning code, _generate_cache_attrs() checks dict of subclass, not the entire class

    def __init__(self, **kwargs):
        IngresDialect.__init__(self, **kwargs)

    @classmethod
    def dbapi(cls):
        try:
            driver = __import__(Ingres_pyodbc.driver)
        except ModuleNotFoundError:
            # fallback to pure Python version
            Ingres_pyodbc.driver = 'pypyodbc'
            driver = __import__(Ingres_pyodbc.driver)
        return driver

    def create_connect_args(self, url):
        opts = url.translate_connect_args(username='uid', password='pwd', host='vnode')
        driver_name = os.environ.get('SQLALCHEMY_INGRES_ODBC_DRIVER_NAME') or 'Actian'  # TODO search driver list for Ingres and Actian, also attempt to find local version using II_INSTALLATION symbol table (if available)

        conn_list = []
        conn_list.append('Driver={' + driver_name + '}')  # FIXME using concat for now
        conn_list.append('Database=' + url.database)
        if not url.host:
            conn_list.append('Server=(local)')
        else:
            #conn_list.append('Server=' + url.host)  # for vnodes only - FIXME look at handling vnodes
            conn_list.append('HostName=' + url.host)
            conn_list.append('ListenAddress=' + str(url.port))
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
