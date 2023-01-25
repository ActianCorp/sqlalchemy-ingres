Avalanche, Actian X, Ingres, and Vector dialect for [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) CPython 3.x (and 2.7).

For more information about SQLAlchemy see:

  * https://github.com/sqlalchemy/sqlalchemy
  * https://www.sqlalchemy.org/
  * https://pypi.org/project/SQLAlchemy/

Originally developed to work against SQLAlchemy 0.6 and Ingres 9.2. Current work-in-progress with:

  * SQLAlchemy 1.3.16 and 1.4.36
  * Avalanche, Ingres 11.x, Vector 5.1, and Vector 6.x - via ODBC

The current Ingres dialect code is built to work with SQLAlchemy version `1.x` and will produce runtime errors if attempting to use it with the forth-coming `2.x` version of SQLAlchemy (for more information see [issue 5](https://github.com/clach04/ingres_sa_dialect/issues/5)).

It is important to be aware of which version of SQLAlchemy is installed. Version pinning provides the ability to install the desired version explicitly.
```
Version pinning examples:

    python -m pip install 'sqlalchemy < 2.0.0'
    python -m pip install sqlalchemy==1.4.42
 ```
 
Jython/JDBC support is currently untested, as the current code relies on zxjdbc it is not recommended this be used (see https://hg.sr.ht/~clach04/jyjdbc for as an alternative that includes full Decimal datatype support).

Known to work with:

  * https://github.com/cloudera/hue
  * https://github.com/apache/superset (see https://github.com/clach04/incubator-superset/tree/vector)
  * https://github.com/catherinedevlin/ipython-sql / Jupyter/IPython notebooks (see https://github.com/catherinedevlin/ipython-sql/pull/196 - or use `%config SqlMagic.autocommit=False`
      * Until ipython-sql 0.4.1 is released, to avoid workaround issue; `pip install git+https://github.com/catherinedevlin/ipython-sql.git`
  * https://github.com/wireservice/csvkit (see https://github.com/wireservice/agate-sql/pull/36)

--------------------------------------------------------

-   [Quickstart](#quickstart)
-   [Development instructions](#development-instructions)
    -   [Quick python test](#quick-python-test)
    -   [Troubleshooting](#troubleshooting)
    -   [Running SA test suite](#running-sa-test-suite)

--------------------------------------------------------

## Quickstart

TL;DR

Install/setup:

    python -m pip install pyodbc sqlalchemy
    git clone https://github.com/clach04/ingres_sa_dialect.git
    cd ingres_sa_dialect
    python -m pip install -e .


Demo Sample / Sanity check:

Linux/Unix

    export SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=INGRES Y1
    # or what ever the ODBC Driver name is; Actian, Ingres, etc.
    # Only needed if program/environment is unable to identify the correct driver.

Windows:

    SET SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=INGRES Y1
    REM or what ever the ODBC Driver name is; Actian, Ingres, etc.
    REM Only needed if program/environment is unable to identify the correct driver.

NOTE ODBC Driver should be the same bitness as the Python interpreter. That is:

  * for 64-bit Python ensure a 64-bit ODBC driver is available.
  * For 32-bit Python ensure a 32-bit ODBC driver is available.

Assuming local DBMS, python session:

    Python 3.7.3 (v3.7.3:ef4ec6ed12, Mar 25 2019, 22:22:05) [MSC v.1916 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import sqlalchemy
    >>> engine = sqlalchemy.create_engine('ingres:///iidbdb')  # local DBMS
    >>> connection = engine.connect()
    >>> for row in connection.execute(sqlalchemy.text('SELECT count(*) FROM iidatabase')):
    ...     print(row)
    ...
    (33,)


## Development instructions

Right now this is for dev purposes so install SQLAlchemy as per normal, for example:

    python -m pip install sqlalchemy

or for dev testing and modifying/running tests:

    git clone -b rel_1_4_42 https://github.com/sqlalchemy/sqlalchemy.git
    cd sqlalchemy
    #pip install -e .
    python -m pip install -e .   # https://adamj.eu/tech/2020/02/25/use-python-m-pip-everywhere/

Ingres dialect tested with pyodbc and pypyodbc (pypyodbc useful for debugging, to see what SQLAlchemy is calling with):

    pip install pyodbc

Download Ingres dialect for SQLAlchemy:

    git clone https://github.com/clach04/ingres_sa_dialect.git

Setup for dev use:

    cd ingres_sa_dialect
    python -m pip install -e .

Demo/Test:

Ensure Ingres ODBC driver is available, Ingres sqlalchemy defaults to using "Ingres" ODBC driver, ensure this is the same bit-age as the Python interpreter. For example, for 64-bit Python, ensure ODBC Driver called "Ingres" is also 64-bit.

ODBC Driver name can be overridden via environment variable `SQLALCHEMY_INGRES_ODBC_DRIVER_NAME`, for example:

Windows 64-bit:

    set SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=Ingres CS
    REM Only needed if program/environment is unable to identify the correct driver.

Windows 32-bit:

    set SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=Ingres CR
    REM Only needed if program/environment is unable to identify the correct driver.

Under Linux/Unix check ODBC settings and if using UnixODBC, check how wide-char support was built, recommendation for out-of-box Linux distributions:

```shell
# Most Linux distros build UnixODBC with non-default build options
export II_ODBC_WCHAR_SIZE=2

# set variables for ODBC config
export ODBCSYSINI=$II_SYSTEM/ingres/files
export ODBCINI=$II_SYSTEM/ingres/files/odbc.ini
```

### Quick python test

```python
import sys
import sqlalchemy
#import ingres_sa_dialect

print('Python %s on %s' % (sys.version, sys.platform))
print('SQLAlchemy %r' % sqlalchemy.__version__)
con_str = 'ingres:///demodb'  # local demodb
#con_str = 'ingres://dbuser:PASSWORD@HOSTNAME:27832/db'  # remote database called "db"
print(con_str)
# If the next line is uncommented, need to also uncomment: import ingres_sa_dialect
#print(ingres_sa_dialect.base.dialect().create_connect_args(url=sqlalchemy.engine.make_url(con_str)))

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
