Ingres dialect for SQLAlchemy https://github.com/sqlalchemy/sqlalchemy.

Originally developed to work against SQLAlchemy 0.6 and Ingres 9.2

Current work-in-progress with:

  * SQLAlchemy 1.3.16 and 1.4.0b1
  * Avalanche, Ingres 11.1, Vector 5.1, and Vector 6.0 - via ODBC

Known to work with:

  * https://github.com/cloudera/hue
  * https://github.com/apache/superset
  * https://github.com/catherinedevlin/ipython-sql / Jupyter/IPython notebooks (see https://github.com/catherinedevlin/ipython-sql/pull/196 - or use `%config SqlMagic.autocommit=False`

## Development instructions

Right now this is for dev purposes so install SQLAlchemy as per normal, for example:

    pip install sqlalchemy

or for dev testing and modifying/running tests:

    git clone https://github.com/sqlalchemy/sqlalchemy.git
    cd sqlalchemy
    #pip install -e .
    python -m pip install -e .   # https://adamj.eu/tech/2020/02/25/use-python-m-pip-everywhere/

Ingres dialect tested with pyodbc and pypyodbc (pypyodbc useful for debugging, to see what SQLAlchemy is calling with):

    pip install pyodbc

Download Ingres dialect for SQLAlchemy:

    git clone https://github.com/clach04/ingres_sa_dialect.git

Setup for dev use:

    cd ingres_sa_dialect
    pip install -e .

Demo/Test:

Ensure Ingres ODBC driver is available, Ingres sqlalchemy defaults to using "Ingres" ODBC driver, ensure this is the same bit-age as the Python interpreter. For example, for 64-bit Python, ensure ODBC Driver called "Ingres" is also 64-bit.

ODBC Driver name can be overridden via environment variable `SQLALCHEMY_INGRES_ODBC_DRIVER_NAME`, for example:

Windows 64-bit:

    set SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=Ingres CS

Windows 32-bit:

    set SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=Ingres CR

Under Linux/Unix check ODBC settings and if using UnixODBC, check how wide-char support was built, recommendation for out-of-box Linux distributions:

```shell
# Most Linux distros build UnixODBC with non-default build options
export II_ODBC_WCHAR_SIZE=2

# set variables for ODBC config
export ODBCSYSINI=$II_SYSTEM/ingres/files
export ODBCINI=$II_SYSTEM/ingres/files/odbc.ini
```

Quick python test:

```python
import sys
import sqlalchemy

print('Python %s on %s' % (sys.version, sys.platform))
print(sqlalchemy.__version__)
con_str = 'ingres:///demodb'  # local demodb
#con_str = 'ingres://dbuser:PASSWORD@HOSTNAME:27832/db'  # remote database called "db"
engine = sqlalchemy.create_engine(con_str)
connection = engine.connect()
query = 'SELECT * FROM iidbconstants'
for row in connection.execute(sqlalchemy.text(query)):
    print(row)
```

### Troubleshooting

Getting error:

    sqlalchemy.exc.DatabaseError: (pypyodbc.DatabaseError) ('08004', '[08004] [Actian][Ingres ODBC Driver][INGRES]Requested association partner is unavailable')

1. DBMS may not be running or accesible (e.g. network error).
2. Could be using a Driver name that is not available (or the wrong number of bits, e.g. 32-bit versus 64-bit or vice-versa), or wrong environment (e.g. multiple DBMS/client installations). Solution, make use of environment variable `SQLALCHEMY_INGRES_ODBC_DRIVER_NAME` either in the environment or in Python code, e.g:

    ```python
    import os; os.environ['SQLALCHEMY_INGRES_ODBC_DRIVER_NAME'] = 'Ingres X2'  # Etc. where X2 is the installation id (output from, "ingprenv II_INSTALLATION")
    ```

### Running SA test suite

NOTE below is for Python 2.7 and 3.4, can remove version pin for current python. Mock appears to be a dependency that is not pulled in for py2.7

    python -m pip  install --upgrade pip
    python -m pip  install tox "pytest==4.6"
    python -m pip  install mock

Setup test config

    $ cat test.cfg
    # test.cfg file
    # see README.unittests.rst
    #       pytest --db sqlite_file
    [db]
    sqlite_file=sqlite:///querytest.sqlite3

    # local
    ingres_odbc=ingres:///sa

Code change needed to SA:

    diff --git a/test/requirements.py b/test/requirements.py
    index cf9168f5a..fcc4f37a0 100644
    --- a/test/requirements.py
    +++ b/test/requirements.py
    @@ -394,6 +394,9 @@ class DefaultRequirements(SuiteRequirements):
             elif against(config, "oracle"):
                 default = "READ COMMITTED"
                 levels.add("AUTOCOMMIT")
    +        elif against(config, "ingres"):
    +            default = "READ COMMITTED"
    +            levels.add("AUTOCOMMIT")  # probably needed, not sure what this is though - assuming tests are not commiting and expecting autocommit semantics
             else:
                 raise NotImplementedError()

Run (all) tests.
    pytest --db ingres_odbc --junit-xml=all_results_junit.xml --maxfail=12000
