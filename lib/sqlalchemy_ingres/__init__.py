# ingres/__init__.py
# Copyright 2020 Actian Corporation
#
# This module is part of SQLAlchemy and is released under
# the Apache-2.0 License: https://opensource.org/license/apache-2-0/

from sqlalchemy_ingres import base, ingresdbi, pyodbc  # , zxjdbc  # does not appear to be in SQLAlchemy 1.4.0b1

from ._version import __version__, __version_info__

base.dialect = pyodbc.Ingres_pyodbc
