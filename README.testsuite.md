
## SQLAlchemy Dialect Compliance Suite
### Overview and Setup
SQLAlchemy includes a [dialect compliance suite](https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite) that is usable by third party libraries, in the source tree at lib/sqlalchemy/testing/suite. There's no need for a third party dialect to run through SQLAlchemy's full testing suite, as a large portion of these tests do not have dialect-sensitive functionality. The "dialect compliance suite" should be viewed as the primary target for new dialects.

_(The above text is from: [README.dialects.rst](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.dialects.rst))_

#### Environment and Packages
These steps have been tested using the following environment:

    Microsoft Windows [Version 10.0.19045.4170]
    Ingres II 11.2.0 (a64.win/100) 15807
    set SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=Actian II
    Python 3.10.7
    Packages:
      mock              5.1.0
      packaging         24.0
      pip               24.0
      pluggy            1.5.0
      pyodbc            5.1.0
      pyproject-api     1.6.1
      pypyodbc          1.3.6
      pytest            8.2.0
      setuptools        63.2.0
      SQLAlchemy        2.0.29.dev0
      sqlalchemy-ingres 0.0.7.dev3
      tox               4.15.0

#### Configuration
DSN and directive for using the Ingres Requirements class in requirements.py:

    [db]
    ingres_odbc=ingres:///sqatestdb
    # ingres_odbc=ingres://testuid:testpwd@testhost:21064/testdb

    [sqla_testing]
    requirement_cls=sqlalchemy_ingres.requirements:Requirements

#### Execution Example
The SQLAlchemy [dialect compliance suite](https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite) contains many test classes and most of these classes run multiple tests. At the time of this writing, the entire suite contains over 1500 individual tests.

This example will run all tests of the class: `DifficultParametersTest`

Contents of file test_suite_area.py:

    from sqlalchemy.testing.suite import (DifficultParametersTest)

Command to execute tests:

    pytest --db ingres_odbc --maxfail=100 test_suite_area.py --tb=no

### Known Issues

#### Use of Alternate Schemas
Several tests require alternate usernames or schemas to be present, which are used to test dotted-name access scenarios. On some databases such as Oracle these are usernames, and others such as PostgreSQL and MySQL they are schemas. The requirement applies to all backends except SQLite and Firebird. The names are:

    test_schema
    test_schema_2 (only used on PostgreSQL and mssql)

Please refer to your vendor documentation for the proper syntax to create these namespaces - the database user must have permission to create and drop tables within these schemas. Its perfectly fine to run the test suite without these namespaces present, it only means that a handful of tests which expect them to be present will fail.

Added a new flag to .DefaultDialect called supports_schemas; third party dialects may set this flag to False to disable SQLAlchemy's schema-level tests when running the test suite for a third party dialect.

_(The above text about alternate schemas is taken from the following SQLAlchemy GitHub pages)_

 [README.unittests.rst](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.unittests.rst)
[changelog_14.rst](https://github.com/sqlalchemy/sqlalchemy/blob/main/doc/build/changelog/changelog_14.rst)

**Ingres Dialect Behavior**
The Ingres dialect disables the ability to run tests that use alternate schemas with the setting `supports_schemas = False` in class `IngresDialect`.

