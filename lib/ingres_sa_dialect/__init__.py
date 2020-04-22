# ingres/__init__.py
# Copyright 2020 Actian Corporation
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
from ingres_sa_dialect import base, ingresdbi, pyodbc  # , zxjdbc  # does not appear to be in SQLAlchemy 1.4.0b1

base.dialect = pyodbc.Ingres_pyodbc
