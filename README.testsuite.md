# Table of Contents

- [Introduction to the SQLAlchemy Test Suites](#introduction-to-the-sqlalchemy-test-suites)
- [Test Execution](#test-execution)
  * [Environment](#environment)
  * [Quick Instructions for Test Case Setup and Execution](#quick-instructions-for-test-case-setup-and-execution)
  * [Helpful pytest documentation links](#helpful-pytest-documentation-links)
- [Configuration Variations and Impact on Expected Results](#configuration-variations-and-impact-on-expected-results)
  * [Requirements Class](#requirements-class)
- [Notes about Dialect API Methods](#notes-about-dialect-api-methods)
  * [get_unique_constraints](#get_unique_constraints)
- [Known Issues](#known-issues)
  * [Use of Alternate Schemas](#use-of-alternate-schemas)
  * [UNION clauses involving SELECT statements containing individual ORDER BY clauses](#union-clauses-involving-select-statements-containing-individual-order-by-clauses)
  * [Self-Referencing Referential Constraints](#self-referencing-referential-constraints)
  * [Unique Constraints and Null Values](#unique-constraints-and-null-values)

--------------------------------------------------------

## Introduction to the SQLAlchemy Test Suites

The SQLAlchemy GitHub repository contains two test suites:

1. **Dialect Compliance Suite**

    - Recommended as the primary testing suite for third party dialects instead of executing SQLAlchemy's full testing suite.  
    - SQLAlchemy version 2.0.36 contains over 1500 unique tests.  
    - Added to SQLAlchemy version 0.8 in 2012 via commit [568de1e](https://github.com/sqlalchemy/sqlalchemy/blob/568de1ef4941dcf366d81ebb46e122f4a973d15a/README.dialects.rst).  
    - Readme: https://github.com/sqlalchemy/sqlalchemy/blob/main/README.dialects.rst  
    - Location of tests: https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite  

2. **Unit Tests**

    - Separate from the dialect compliance suite.  
    - A large portion of these tests do not have dialect-sensitive functionality.  
    - SQLAlchemy version 2.0.36 contains over 30K unique tests.  
    - Readme: https://github.com/sqlalchemy/sqlalchemy/blob/main/README.unittests.rst  
    - Location of Tests: https://github.com/sqlalchemy/sqlalchemy/tree/main/test  

## Test Execution

### Environment

The test suite operations described in this document have been tested in various environments including the following:

**Client:**

      Microsoft Windows version 10
      Python 3.10.x
      Python virtual environment
      Python packages including: mock, tox, pytest, pyodbc
      SQLAlchemy 1.x, 2.x
      SQLAlchemy-Ingres connector

Note that older versions of Python (e.g. 2.7 and 3.4) might require an older version of pytest. 
If needed, the package version can be specified. For example: `python -m pip install "pytest==4.6"`

**Databases:**

      Ingres 11.x, 12.x on Windows
      Vector 6.x and 7.x on Ubuntu

### Quick Instructions for Test Case Setup and Execution

Windows example to set up and run SQLAlchemy tests from the latest default branch.  

The example assumes a local Ingres instance is running and contains a (preferably empty) database called `testdb`.

    C:\test> python -m venv .venv
    C:\test> .\.venv\Scripts\activate.bat
    C:\test> python -m pip install --upgrade pip pytest mock tox pyodbc pypyodbc sqlalchemy-ingres

    C:\test> git clone https://github.com/sqlalchemy/sqlalchemy.git
    C:\test> python -m pip install -e sqlalchemy

    C:\test> cd sqlalchemy

    C:\test\sqlalchemy> cat test.cfg   (Create this file using your favorite editor)
    [db]
    ingres_odbc=ingres:///testdb

    # Other uri examples
    alt_ingres_odbc=ingres://uid123:pwd123@testhost:21064/testdb
    postgres_dbapi=postgresql+psycopg2://postgres:pwd123@localhost/testdb
    sqlite_mem=sqlite:///:memory:
    sqlite_file=sqlite:///querytest.sqlite3

    [sqla_testing]
	#See later discussion about the impact of using Requirements
    #requirement_cls=sqlalchemy_ingres.requirements:Requirements	

    C:\test\sqlalchemy> set SQLALCHEMY_INGRES_ODBC_DRIVER_NAME=Actian II   (Use appropriate ODBC driver)

#### Code changes needed for SQLAlchemy 1.x unit tests

The following SQLAlchemy code changes are required only to run the SQLAlchemy 1.x unit tests.
The code changes are not required with the SQLAlchemy 1.x dialect compliance suite.
The code changes are not required for any SQLAlchemy 2.x testing (unit or dialect compliance tests).

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

#### Execute all SQLAlchemy tests

    C:\test\sqlalchemy> pytest --maxfail=10000 --db ingres_odbc

#### Execute SQLAlchemy Dialect Compliance Suite tests

    C:\test\sqlalchemy> pytest --maxfail=10000 --db ingres_odbc .\test\dialect\test_suite.py

#### Execute SQLAlchemy Unit tests

    C:\test\sqlalchemy> pytest --maxfail=10000 --db ingres_odbc .\test

### Helpful pytest documentation links
 - [https://docs.pytest.org/en/stable/](https://docs.pytest.org/en/stable/)
 - [https://naveens33.github.io/pytest-tutorial/docs/commandlineoptions.html](https://naveens33.github.io/pytest-tutorial/docs/commandlineoptions.html)

#### Sample of pytest arguments (from pytest --help)

    --db=DB           Use prefab database uri.
    --maxfail=NUM     Exit after first NUM failures or errors
    -k EXPRESSION     Only run tests which match the given substring expression
    --tb=style        Traceback print mode (auto/long/short/line/native/no)
    -v, -vv           Increase verbosity
    --junit-xml=path  Create junit-xml style report file at given path


## Configuration Variations and Impact on Expected Results

There are a variety of ways to execute SQLAlchemy tests with Actian databases.
This section provides information to help understand expected results for various configurations.

The provided information is current for version 0.0.10 of the Ingres connector.

PR [42](https://github.com/ActianCorp/sqlalchemy-ingres/pull/42) contained changes to the SQLAlchemy Ingres connector that included new import statements. These changes broke compatibility with SQLAlchemy 1.4. PR [69](https://github.com/ActianCorp/sqlalchemy-ingres/pull/69) fixed this problem so that the Ingres connector once again works with SQLAlchemy 1.x, retains compatibility with SQLAlchemy 2.x, and is able to run the SQLAlchemy dialect compliance suite and the unit tests for SQLAlchemy versions 1.x and 2.x.


### Requirements Class

An important element in test case behavior is the Ingres connector `Requirements` class that is defined in `requirements.py`
 and sub-classed from `SuiteRequirements` found in `sqlalchemy.testing.requirements`
 that was added via PR [49](https://github.com/ActianCorp/sqlalchemy-ingres/pull/49).
 
The Ingres connector Requirements class allows the SQLAlchemy testing framework to
 better understand the capabilities of the Ingres dialect which in turn provides more accurate results
 when running the SQLAlchemy dialect compliance suite with Ingres databases.

SQLAlchemy issue [5174](https://github.com/sqlalchemy/sqlalchemy/issues/5174) contains a brief discussion by the SQLAlchemy team on
 whether dialects should each have their own requirements.py.
 The team seemingly decided against that idea and instead has opted to explicitly configure behavior options only for the bundled dialects.
 For example, see [requirements.py](https://github.com/sqlalchemy/sqlalchemy/blob/main/test/requirements.py) which defines behavioral requirements
 for `postgresql`, `mysql`, `mariadb`, `sqlite`, `oracle`, and `mssql`.  
 e.g.  

    @property
    def unique_constraints_reflect_as_index(self):
        return only_on(["mysql", "mariadb", "oracle", "postgresql", "mssql"])

For now, all dialects other than the ones referred to in the SQLAlchemy requirements.py should implement their own Requirements class,
 which in fact has been done with the SQLAlchemy dialects for PyAthena, Snowflake, CockroachDB, Firebird, MonetDB, Sybase SQL Anywhere and many others.

It is important to understand the impact of using the Ingres connector Requirements class.

SQLAlchemy<br>Version | Test Suite | Requirements<br>Enabled | Requirements<br>Disabled
--|--|--|--
1.4.54 | Dialect Compliance Suite | Good results | Will not execute due to many<br>NotImplementedError
1.4.54 | Unit Tests | Will not execute due to missing requirements | Will not execute due to missing requirements
2.0.36 | Dialect Compliance Suite | Good results | Poor pass rate due to many errors
2.0.36 | Unit Tests | Will not execute due to missing requirements | Tests execute with good results

The Ingres connector Requirements class is included/enabled by having the following lines present in the file `test.cfg`.
To disable the Requirements class, simply comment out or remove these lines from `test.cfg`.  

    [sqla_testing]
    requirement_cls=sqlalchemy_ingres.requirements:Requirements

## Notes about Dialect API Methods

### get_unique_constraints

Method **IngresDialect::get_unique_constraints** returns a list of dictionaries, with each dictionary key containing the constraint name and each dictionary value containing a list of the constraint column(s).

If the constraint name was auto-generated by the SQL engine (versus explicitly named in the application's CREATE TABLE statement), **get_unique_constraints** returns the constraint name as `None`.

Example of constraint data returned from **IngresDialect::get_unique_constraints**

    [ {'name': None, 'column_names': ['data']},
      {'name': 'zz_dingalings_multiple', 'column_names': ['address_id', 'dingaling_id']},
      {'name': 'user_tmp_uq_main', 'column_names': ['name']} ]


## Known Issues

### Use of Alternate Schemas

When running the SQLAlchemy [dialect compliance suite](https://github.com/sqlalchemy/sqlalchemy/tree/main/lib/sqlalchemy/testing/suite), quite a few tests fail with some form of the following error:

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
Per discussion in [11366](https://github.com/sqlalchemy/sqlalchemy/discussions/11366) and additional research in internal ticket [II-14148](https://actian.atlassian.net/browse/II-14148), the setting `supports_schemas = False` was added to the IngresDialect class via PR [50](https://github.com/ActianCorp/sqlalchemy-ingres/pull/50) so that when the dialect compliance suite is executed, any tests that use alternate schemas will be skipped.

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

The SQLAlchemy class method `SQLCompiler::order_by_clause` allows dialects to customize how ORDER BY is rendered for SQL statements.
 In theory, one could override this method via `IngresSQLCompiler::order_by_clause` to avoid adding the ORDER BY clause to SELECT statements that are subqueries.
 However, for this method override to be viable, it would also need to know whether the current subquery is involved in a UNION clause, which might not be easy or even possible.

In addition, we probably don't want the Ingres dialect to forcibly exclude the ORDER BY clause from the SQL statement
 when the application code explicitly specifies using an ORDER BY for a SELECT statement that will be involved in a UNION clause.

Therefore, the proper behavior should probably be what occurs already against Ingres, which is a syntax error informing the user
 that the ORDER BY clause is not allowed for a SELECT statement involved in a UNION clause.

Internal issue [II-14232](https://actian.atlassian.net/browse/II-14232)

### Self-Referencing Referential Constraints

 The following example error occurs when trying to execute CREATE TABLE statements using self-referencing referential constraints against Vector:

    pyodbc.Error: ('50000', "[50000] [Actian][Actian AC ODBC Driver][INGRES]CREATE/ALTER TABLE:
    You cannot create a self referencing referential constraint on table 'node' in schema 'actian'
    because it is an X100 table. (328949) (SQLExecDirectW)")

This is mostly because the test suite tries to create a number of tables that use self-referencing referential constraints,
 which are allowed with Ingres, but not allowed with X100 (i.e. Vector) tables.

In addition, there are a large number of SQLAlchemy tests that attempt to use the missing tables which leads to additional failures/errors when trying to run these tests.

### Unique Constraints and Null Values

The SQLAlchemy `get_multi_columns` tests expect that null values are allowed for any column that is part of a unique constraint.

Ingres tables do _not_ allow columns that are specified as UNIQUE to contains nulls.
 See https://docs.actian.com/actianx/12.0/index.html#page/SQLRef/Constraints.htm#ww124554
 Thus, several SQLAlchemy `get_multi_columns` inspection tests will fail even though the results returned by the dialect are correct.

It is worth noting that X100 tables _do_ allow columns specified as unique to contain null values.
 Similarly, other third party databases such as PostgreSQL also allow column members of unique constraints to be null.
 See https://www.postgresql.org/docs/16/sql-createtable.html

