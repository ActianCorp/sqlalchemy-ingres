# Introduction

The SQLAlchemy GitHub repository contains two test suites:

 - **Dialect Compliance Suite**
     - [Readme](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.dialects.rst)
     - [Tests](https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite)

 - **Unit Tests**
     - [Readme](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.unittests.rst)
     - [Tests](https://github.com/sqlalchemy/sqlalchemy/tree/main/test)

The dialect compliance suite was initially added to SQLAlchemy version 0.8 in 2012 via commit [568de1e](https://github.com/sqlalchemy/sqlalchemy/blob/568de1ef4941dcf366d81ebb46e122f4a973d15a/README.dialects.rst).

In order to run the dialect compliance suite, it is necessary that dialects have a `requirements.py`. A `requirements.py` file was added to SQLAlchemy Ingres connector 0.0.7 in May 2024 via PR [49](https://github.com/ActianCorp/sqlalchemy-ingres/pull/49).

The SQLAlchemy unit tests are separate from the dialect compliance suite. The number of tests varies depending on the exact version of SQLAlchemy. For recent releases of SQLAlchemy 2.x, there are over 30K unit tests while the dialect compliance suite contains fewer than 2K tests.

In PR [42](https://github.com/ActianCorp/sqlalchemy-ingres/pull/42), changes were made to the SQLAlchemy Ingres connector that included new import statements. These changes broke compatibility with SQLAlchemy 1.4. PR [69](https://github.com/ActianCorp/sqlalchemy-ingres/pull/69) fixed this problem so that the Ingres connector once again works with SQLAlchemy 1.x, retains compatibility with SQLAlchemy 2.x, and is able to run the SQLAlchemy dialect compliance suite and the unit tests for SQLAlchemy versions 1.x and 2.x.


# SQLAlchemy Dialect Compliance Suite
## Overview and Setup

The following text is from the page [README.dialects.rst](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.dialects.rst) of the SQLAlchemy GitHub repository.

> SQLAlchemy includes a [dialect compliance suite](https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite) that is usable by third party libraries, in the source tree at lib/sqlalchemy/testing/suite. There's no need for a third party dialect to run through SQLAlchemy's full testing suite, as a large portion of these tests do not have dialect-sensitive functionality. The "dialect compliance suite" should be viewed as the primary target for new dialects.

### Environment and Packages
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

### Configuration
DSN and directive for using the Ingres Requirements class in requirements.py:

    [db]
    ingres_odbc=ingres:///sqatestdb
    # ingres_odbc=ingres://testuid:testpwd@testhost:21064/testdb

    [sqla_testing]
    requirement_cls=sqlalchemy_ingres.requirements:Requirements

### Execution Example
The SQLAlchemy [dialect compliance suite](https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite) contains many test classes and most of these classes run multiple tests. At the time of this writing, the entire suite contains over 1500 individual tests.

This example will run all tests of the class: `DifficultParametersTest`

Contents of file test_suite_area.py:

    from sqlalchemy.testing.suite import (DifficultParametersTest)

Command to execute tests:

    pytest --db ingres_odbc --maxfail=100 test_suite_area.py --tb=no

## Notes about Dialect API Methods

### get_unique_constraints()

Method **IngresDialect::get_unique_constraints** returns a list of dictionaries, with each dictionary key containing the constraint name and each dictionary value containing a list of the constraint column(s).

If the constraint name was auto-generated by the SQL engine (versus explicitly named in the application's CREATE TABLE statement), **get_unique_constraints** returns the constraint name as `None`.

Example of constraint data returned from **IngresDialect::get_unique_constraints**

    [ {'name': None, 'column_names': ['data']},
      {'name': 'zz_dingalings_multiple', 'column_names': ['address_id', 'dingaling_id']},
      {'name': 'user_tmp_uq_main', 'column_names': ['name']} ]

## Known Issues

### Use of Alternate Schemas

When running the SQLAlchemy [dialect compliance suite](https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite), quite a few tests would fail with some form of the following error:

    sqlalchemy.exc.ProgrammingError: (pyodbc.ProgrammingError)
    ('42503', "[42503] [Actian][Actian II ODBC Driver][INGRES]
    CREATE TABLE: You may not create an object owned by 'test_schema'. (328737) (SQLExecDirectW)")
    [SQL:
    CREATE TABLE test_schema.test_table (
        id INTEGER GENERATED BY DEFAULT AS IDENTITY NOT NULL,
        data VARCHAR(50),
        PRIMARY KEY (id) )

The reason for the error is that the affected tests attempt to create and drop tables owned under schemas different than the current user.

Ingres does not support this kind of operation except in rare instances where the current user has security administrator and operator privilege or who is the DBA of the database. The user must then use the `SET SESSION AUTHORIZATION ...` command to set the effective user for the current session.

The following text about alternate schemas is taken from these SQLAlchemy GitHub pages: [README.unittests.rst](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.unittests.rst), [changelog_14.rst](https://github.com/sqlalchemy/sqlalchemy/blob/main/doc/build/changelog/changelog_14.rst)

> Several tests require alternate usernames or schemas to be present, which are used to test dotted-name access scenarios. On some databases such as Oracle these are usernames, and others such as PostgreSQL and MySQL they are schemas. The requirement applies to all backends except SQLite and Firebird. The names are:  
>
>    test_schema
>    test_schema_2 (only used on PostgreSQL and mssql)
> 
> Please refer to your vendor documentation for the proper syntax to create these namespaces - the database user must have permission to create and drop tables within these schemas. Its perfectly fine to run the test suite without these namespaces present, it only means that a handful of tests which expect them to be present will fail.
> 
> Added a new flag to .DefaultDialect called supports_schemas; third party dialects may set this flag to False to disable SQLAlchemy's schema-level tests when running the test suite for a > third party dialect.

#### Flag added to the Ingres Dialect
Per discussion in [11366](https://github.com/sqlalchemy/sqlalchemy/discussions/11366) and additional research in internal ticket [II-14148](https://actian.atlassian.net/browse/II-14148), the setting `supports_schemas = False` will be added to the IngresDialect class via PR [50](https://github.com/ActianCorp/sqlalchemy-ingres/pull/50) so that when the dialect compliance suite is executed, any tests that use alternate schemas will be skipped.

Example comparison of results before and after adding the setting `supports_schemas = False`

Result | Before | After | Diff  
-- | -- | -- | --
Total Tests | 1531 | 1531 | -  
Passed | 336 | 473 | +137  
Failed | 63 | 173 | +110  
Errors | 798 | 30 | -768  
Skipped | 334 | 855 | +521  
Run Time | 17m 25s | 42s | -16m 43s  

### UNION clauses involving SELECT statements containing individual ORDER BY clauses

Several compliance tests FAIL with `Syntax error on '"ORDER'` caused by a generated SQL statement having SELECT queries that individually contain ORDER BY clauses and are involved in a UNION clause. This type of SQL statement is not allowed by Ingres.  See doc [ref](https://docs.actian.com/actianx/12.0/index.html#page/OpenSQLRef/UNION_Clause.htm).

Known compliance tests that fail due to this issue:

    test_select.py
        CompoundSelectTest::test_limit_offset_in_unions_from_alias
        CompoundSelectTest::test_limit_offset_selectable_in_unions
        CompoundSelectTest::test_order_by_selectable_in_unions
        CompoundSelectTest::test_limit_offset_aliased_selectable_in_unions

    test_deprecations.py
        DeprecatedCompoundSelectTest::test_limit_offset_selectable_in_unions
        DeprecatedCompoundSelectTest::test_order_by_selectable_in_unions
        DeprecatedCompoundSelectTest::test_limit_offset_aliased_selectable_in_unions

Code example from [test_select.py](https://github.com/sqlalchemy/sqlalchemy/blob/b277e0d501c5d975a8af84e0827dd348ad375acc/lib/sqlalchemy/testing/suite/test_select.py#L928)

    def test_limit_offset_in_unions_from_alias(self):
        table = self.tables.some_table
        s1 = select(table).where(table.c.id == 2).limit(1).order_by(table.c.id)
        s2 = select(table).where(table.c.id == 3).limit(1).order_by(table.c.id)
        u1 = union(s1, s2).alias()

The SQLAlchemy class method `SQLCompiler::order_by_clause` allows dialects to customize how ORDER BY is rendered for SQL statements. In theory, one could override this method via `IngresSQLCompiler::order_by_clause` to avoid adding the ORDER BY clause to SELECT statements that are subqueries. However, for this method override to be viable, it would also need to know whether the current subquery is involved in a UNION clause, which might not be easy or even possible.

In addition, we probably don't want the Ingres dialect to forcibly exclude the ORDER BY clause from the SQL statement when the application code explicitly specifies using an ORDER BY for a SELECT statement that will be involved in a UNION clause.

Therefore, the proper behavior should probably be what occurs already against Ingres, which is a syntax error informing the user that the ORDER BY clause is not allowed for a SELECT statement involved in a UNION clause.

Internal issue [II-14232](https://actian.atlassian.net/browse/II-14232)


# SQLAlchemy Unit Tests

The SQLAlchemy unit tests are found in this [folder](https://github.com/sqlalchemy/sqlalchemy/tree/main/test).

Instructions for running the unit tests are [here](https://github.com/sqlalchemy/sqlalchemy/blob/main/README.unittests.rst).

## Quick Instructions for Windows

Example of how to set up and run the full unit tests of the latest SQLAlchemy default branch.
The example assumes a local Ingres instance is running and contains a database called `testdb`.

    C:\test> python -m venv .venv
    C:\test> .\.venv\Scripts\activate.bat
    C:\test> python -m pip install --upgrade pip pytest mock tox pyodbc pypyodbc sqlalchemy-ingres

    C:\test> git clone https://github.com/sqlalchemy/sqlalchemy.git
    C:\test> python -m pip install -e sqlalchemy

    C:\test> cd sqlalchemy

    C:\test\sqlalchemy> cat test.cfg   (Need to have first created this file using your favorite editor)
    [db]
    ingres_odbc=ingres:///testdb

    C:\test\sqlalchemy> set SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=Actian II   (Use appropriate ODBC driver)

    C:\test\sqlalchemy> pytest --maxfail=100 --db ingres_odbc .\test

