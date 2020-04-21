# ingres/__init__.py
# Copyright 2009 Ingres Corporation
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
from ingres_sa_dialect import base, ingresdbi, zxjdbc

base.dialect = ingresdbi.Ingres_ingresdbi
