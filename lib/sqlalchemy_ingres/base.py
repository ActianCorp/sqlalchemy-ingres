# ingres/base.py
#
"""Support for the Ingres Database

Versions
--------

This dialect is tested against Actian Data Platform, Actian X 11.x, Vector 6.x,
and was initially developed with Ingres 9.2.
Some features may not work on earlier versions.
The driver used during testing was pyodbc/pypyodbc and ODBC driver, available from esd.actian.com.
zxjdbc has been tried but not fully tested (and has been removed from later versions of SQLAlchemy).

Connection Strings
------------------

The argument "selectloops=y" should be used for all connections.  The format of the URL is similar
to that for the ingresdbi driver; refer to its documentation for further information.  In general:
ingres://server/database?uid=user;pwd=passwd;selectloops=y

where server is the remote server name, or (LOCAL) if local,
      database is the name of the database to connect to,
      user is the username to connect as, if necessary and
      passwd is the given user's password, if necessary.

"""

import sqlalchemy
from sqlalchemy import types, schema
from sqlalchemy.engine import cursor as _cursor
from sqlalchemy.engine import default, reflection
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import compiler
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.dml import DMLState
from sqlalchemy.sql.selectable import TableClause
from typing import TYPE_CHECKING

try:
    from sqlalchemy.sql._typing import is_sql_compiler
except ImportError:
    is_sql_compiler = None


# TODO review - simplistic approach does not handle '1.4.0b1', consider using https://pypi.org/project/version-parser/
# sqlalchemy_version_tuple = tuple(map(int, sqlalchemy.__version__.split('.')))
sqlalchemy_version_tuple = tuple(
    map(int, sqlalchemy.__version__.split(".", 2)[0:2])
)  # Only care about major and minor

# https://docs.actian.com/actianx/11.1/index.html#page/SQLRef/TRANSACTION_ISOLATION_LEVEL.htm
isolation_lookup = set(
    [
        "READ COMMITTED",
        "READ UNCOMMITTED",
        "REPEATABLE READ",
        "SERIALIZABLE",
    ]
)

ischema_names = {
    "ANSIDATE": types.Date,
    "BIGINT": types.BigInteger,
    "BOOLEAN": types.BOOLEAN,
    "BYTE": types.BINARY,
    "BYTE VARYING": types.BINARY,
    "C": types.TEXT,
    "CHAR": types.CHAR,
    "DATE": types.DateTime,
    "DECIMAL": types.DECIMAL,
    "FLOAT": types.Float,
    "INGRESDATE": types.DateTime,
    "INTEGER": types.Integer,
    "INTERVAL YEAR TO MONTH": types.Interval,
    "INTERVAL DAY TO SECOND": types.Interval,
    "LONG BYTE": types.LargeBinary,
    "LONG NVARCHAR": types.UnicodeText,
    "LONG VARCHAR": types.CLOB,
    "MONEY": types.DECIMAL,
    "NCHAR": types.NCHAR,
    "NVARCHAR": types.NVARCHAR,
    # 'OBJECT_KEY': types.,
    # 'TABLE_KEY':,
    "SMALLINT": types.SmallInteger,
    "TEXT": types.TEXT,
    "TINYINT": types.SmallInteger,  # FIXME this is the wrong size but closest - TODO look at get_dbapi_type() / setinputsizes()
    "TIME WITH TIME ZONE": types.TIME,
    "TIME WITHOUT TIME ZONE": types.TIME,
    "TIME WITH LOCAL TIME ZONE": types.TIME,
    "TIMESTAMP WITH TIME ZONE": types.TIMESTAMP,
    "TIMESTAMP WITHOUT TIME ZONE": types.TIMESTAMP,
    "TIMESTAMP WITH LOCAL TIME ZONE": types.TIMESTAMP,
    "VARCHAR": types.VARCHAR,
}


class _IngresBoolean(types.Boolean):
    def get_dbapi_type(self, dbapi):
        return dbapi.TINYINT

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return value and True or False

        return process

    def bind_processor(self, dialect):
        def process(value):
            if value is True:
                return 1
            elif value is False:
                return 0
            elif value is None:
                return None
            else:
                return value and True or False

        return process


class _IngresDateWithoutTime(types.Date):
    def get_dbapi_type(self, dbapi):
        return dbapi.DATE

    def result_processor(self, dialect):
        def process(value):
            if value is None:
                return None


colspecs = {types.Boolean: _IngresBoolean}


class IngresTypeCompiler(compiler.GenericTypeCompiler):
    def visit_TIME(self, type_):
        if type_.tzinfo is None:
            return "TIME WITHOUT TIME ZONE"
        else:
            return "TIME WITH TIME ZONE"

    def visit_BOOLEAN(self, type_):
        return self.visit_TINYINT(type_)

    def visit_TINYINT(self, type_):
        return "TINYINT"

    def visit_DATETIME(self, type_):
        return "TIMESTAMP"

    def visit_DATE(self, type_):
        return "ANSIDATE"

    def visit_CLOB(self, type_):
        return "LONG VARCHAR"

    def visit_NCLOB(self, type_):
        return "LONG NVARCHAR"

    def visit_BLOB(self, type_):
        return "LONG BYTE"

    def visit_TEXT(self, type_):
        return self.visit_CLOB(type_)

    def visit_DECIMAL(self, type_):
        if type_.precision is None:
            return "DECIMAL"
        elif type_.scale is None:
            return "DECIMAL(%(precision)s)" % {"precision": type_.precision}
        else:
            return "DECIMAL(%(precision)s, %(scale)s)" % {"precision": type_.precision, "scale": type_.scale}

    def visit_unicode(self, type_):
        return self.visit_NVARCHAR(type_)

    def visit_unicode_text(self, type_):
        return self.visit_NCLOB(type_)


class IngresSQLCompiler(compiler.SQLCompiler):
    def visit_sequence(self, seq, **kwargs):
        # NOTE this now silently ignores keyword argument 'literal_binds', etc.
        return "NEXT VALUE FOR %s" % self.preparer.format_sequence(seq)

    def limit_clause(self, select, **kwargs):
        # NOTE this now silently ignores keyword argument 'literal_binds', 'enclosing_alias', 'include_table', etc.
        text = ""
        if not self.is_subquery():
            if is_integer_greater_than_zero(select._offset):
                text += "\nOFFSET %s" % select._offset
            if is_integer_greater_than_zero(select._limit):
                if is_integer_greater_than_zero(select._offset):
                    text += "\nFETCH FIRST %s ROWS ONLY" % select._limit
                else:
                    text += "\nLIMIT %s" % select._limit
        return text

    def get_select_precolumns(self, select, **kwargs):
        # FIXME SA 1.4 code indicates this is going away and being replaced with -- `_expression.Select.prefix_with` should be used for special keywords at the start of a SELECT.
        # NOTE this now silently ignores keyword argument 'literal_binds', 'enclosing_alias', 'eager_grouping', etc.
        s = ""
        if select._distinct and not self.is_subquery():
            s = " DISTINCT "
        return s

    def visit_release_savepoint(self, savepoint_stmt):
        return ""


class _Modify(DDLElement):
    """Represents a MODIFY Statment"""

    __visit_name__ = "modify"

    def __init__(self, target, **kwargs):
        self.target = target
        self.kwargs = kwargs


class IngresDDLCompiler(compiler.DDLCompiler):

    def visit_drop_constraint(self, drop):
        table = drop.element.table
        constr = drop.element
        return "ALTER TABLE %s DROP CONSTRAINT %s %s" % (
            self.preparer.format_table(table),
            self.preparer.format_constraint(constr),
            drop.cascade and "CASCADE" or "RESTRICT",
        )

    def get_column_default_string(self, column):
        """
        import pdb ; pdb.set_trace()
        if isinstance(column.server_default, schema.DefaultClause):
            if isinstance(column.server_default.arg, basestring):
                return "'%s'" % column.server_default.arg
            else:
                return unicode(self._compile(column.server_default.arg, None))
        elif isinstance(column.default, schema.Sequence):
        """
        if isinstance(column.default, schema.Sequence):
            return "NEXT VALUE FOR %s" % self.preparer.format_sequence(column.default)
        else:
            return None

    def get_column_specification(self, column, **kwargs):

        if str(column.type) == "VARCHAR":
            if column.type.length is None:  # If no length is provided for VARCHAR column
                column.type.length = 255  # Set length to 255

        if sqlalchemy_version_tuple >= (2, 0):
            colspec = (
                self.preparer.format_column(column)
                + " "
                + self.dialect.type_compiler_instance.process(column.type, type_expression=column)
            )
        else:  # SQLAlchemy v1.x path
            colspec = (
                self.preparer.format_column(column)
                + " "
                + self.dialect.type_compiler.process(column.type, type_expression=column)
            )

        default = self.get_column_default_string(column)
        if default is not None:
            colspec += " DEFAULT " + default

        if column.computed is not None:
            colspec += " " + self.process(column.computed)

        if column.identity is not None:
            colspec += " " + self.process(column.identity)
        else:
            if (
                column.primary_key
                and column.autoincrement
                and column is column.table._autoincrement_column
                and column.default is None
            ):
                colspec += " GENERATED BY DEFAULT AS IDENTITY"

        # For columns defined as part of a unique constraint:
        #   Ingres tables : column cannot be nullable
        #   X100 tables   : column can be nullable
        # https://docs.actian.com/actianx/12.0/index.html#page/SQLRef/Constraints.htm#ww124554
        if (
            column.identity is not None
            or column.primary_key is True
            or not column.nullable
            or (column.unique is True and self.dialect.iidbcapabilities["DBMS_TYPE"] == "INGRES")
        ):
            colspec += " NOT NULL"
        else:
            for constraint in column.table.constraints:
                if constraint.contains_column(column):  # Maybe redundant since checked again in for loop
                    for constraint_column in constraint:
                        if constraint_column == column:
                            if (
                                constraint_column.nullable is False
                                or constraint_column.unique is True
                                or constraint_column.primary_key is True
                                or isinstance(constraint, sqlalchemy.sql.schema.UniqueConstraint)
                            ):
                                if self.dialect.iidbcapabilities["DBMS_TYPE"] == "INGRES":
                                    colspec += " NOT NULL"
                                    break
        return colspec

    def visit_create_index(self, create):
        text = compiler.DDLCompiler.visit_create_index(self, create)
        index = create.element
        if "ingres_structure" in index.kwargs:
            text += " WITH STRUCTURE=%s" % (index.kwargs["ingres_structure"])
            if "ingres_structure_keys" in index.kwargs:
                if (
                    "ingres_structure_key_unique" in index.kwargs
                    and index.kwargs["ingres_structure_key_unique"]
                ):
                    text += " UNIQUE "
                text += " ON "
                text += ", ".join(["%s" % col for col in index.kwargs["ingres_structure_keys"]])

        return text

    def post_create_table(self, table):
        if "ingres_structure" in table.kwargs:
            _Modify(table, **(table.kwargs)).execute_at("after-create", table)
        return ""

    def visit_modify(self, modify):
        text = "MODIFY %s TO " % modify.target
        if "ingres_structure" in modify.kwargs:
            text += "%s" % modify.kwargs["ingres_structure"]

            if "ingres_structure_keys" in modify.kwargs:
                if (
                    "ingres_structure_key_unique" in modify.kwargs
                    and modify.kwargs["ingres_structure_key_unique"]
                ):
                    text += " UNIQUE "
                text += " ON "
                text += ", ".join(["%s" % col for col in modify.kwargs["ingres_structure_keys"]])
        return text


class IngresExecutionContext(default.DefaultExecutionContext):
    _select_lastrowid = False
    _lastrowid = None

    def __init__(self, *args, **kwargs):
        default.DefaultExecutionContext.__init__(self, *args, **kwargs)

    def fire_sequence(self, seq, type_):
        return self._execute_scalar(
            "SELECT NEXT VALUE FOR %s" % self.dialect.identifier_preparer.format_sequence(seq), type_
        )

    def pre_exec(self):
        if self.isinsert:
            if TYPE_CHECKING:
                if is_sql_compiler:
                    assert is_sql_compiler(self.compiled)
                assert isinstance(self.compiled.compile_state, DMLState)
                assert isinstance(self.compiled.compile_state.dml_table, TableClause)

            tbl = self.compiled.compile_state.dml_table
            id_column = tbl._autoincrement_column

            if id_column is not None:
                insert_has_identity = True

            else:
                insert_has_identity = False

            self._select_lastrowid = (
                not self.compiled.inline
                and insert_has_identity
                and not self.executemany
                and not (
                    self.compiled.effective_returning
                    if sqlalchemy_version_tuple >= (2, 0)
                    else self.compiled.returning
                )
            )

    def post_exec(self):
        conn = self.root_connection

        if self.isinsert or self.isupdate or self.isdelete:
            self._rowcount = self.cursor.rowcount

        if self._select_lastrowid:
            conn._cursor_execute(
                self.cursor,
                "SELECT last_identity() AS lastrowid",
                (),
                self,
            )
            # fetchall() ensures the cursor is consumed without closing it
            row = self.cursor.fetchall()[0]
            if row[0] is not None:
                self._lastrowid = int(row[0])

            self.cursor_fetch_strategy = _cursor._NO_CURSOR_DML
        elif self.compiled is not None:
            if (
                sqlalchemy_version_tuple >= (2, 0)
                and (is_sql_compiler(self.compiled) if is_sql_compiler else True)
                and self.compiled.effective_returning
                or ((self.isinsert or self.isupdate or self.isdelete) and self.compiled.returning)
            ):
                self.cursor_fetch_strategy = _cursor.FullyBufferedCursorFetchStrategy(
                    self.cursor,
                    self.cursor.description,
                    self.cursor.fetchall(),
                )

    def get_lastrowid(self):
        return self._lastrowid


class IngresDialect(default.DefaultDialect):
    name = "ingres"
    default_paramstyle = "qmark"
    max_identifier_length = 32  # FIXME review
    colspecs = colspecs
    ischema_names = ischema_names
    statement_compiler = IngresSQLCompiler
    type_compiler = IngresTypeCompiler
    statement_compiler = IngresSQLCompiler
    ddl_compiler = IngresDDLCompiler
    execution_ctx_cls = IngresExecutionContext
    supports_identity_columns = True
    supports_sequences = True
    supports_unicode_statements = True
    supports_unicode_binds = True
    supports_empty_insert = False
    supports_empty_insert = False
    supports_statement_cache = False  # NOTE this is not actually picked up by SA warning code, _generate_cache_attrs() checks dict of subclass, not the entire class
    supports_schemas = False  # see README.testsuite.md for details
    supports_comments = True
    postfetch_lastrowid = True
    requires_name_normalization = True
    sequences_optional = False
    _isolation_lookup = isolation_lookup
    iidbcapabilities = None
    # TODO get_isolation_level()
    # TODO _check_max_identifier_length()

    def __init__(self, **kwargs):
        default.DefaultDialect.__init__(self, **kwargs)

    def initialize(self, connection):
        super().initialize(connection)
        self._load_iidbcapabilities(connection)

    def _load_iidbcapabilities(self, connection):
        sqltext = """
            SELECT
                cap_capability,
                cap_value
            FROM
                iidbcapabilities"""

        rs = None
        try:
            rs = connection.exec_driver_sql(sqltext)
            self.iidbcapabilities = {}
            for row in rs.fetchall():
                self.iidbcapabilities[row[0].rstrip()] = row[1].rstrip()

            rs.close()
        finally:
            if rs:
                rs.close()

    def get_isolation_level_values(self, connection):
        return list(self._isolation_lookup)

    def _get_column_comment(self, connection, table_name, column_name, schema=None):
        sqltext = """
            SELECT
                long_remark
            FROM
                iidb_subcomments
            WHERE
                object_name = ?
                AND subobject_name = ?"""
        params = (
            self.denormalize_name(table_name),
            self.denormalize_name(column_name),
        )

        if schema:
            sqltext += """
                AND object_owner = ?"""
            params = (*params, self.denormalize_name(schema))

        rs = None
        try:
            rs = connection.exec_driver_sql(sqltext, params)
            row = rs.fetchone()
            if row is not None:
                return row[0]
        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_columns(self, connection, table_name, schema=None, **kw):
        sqltext = """
            SELECT
                column_name,
                column_datatype,
                column_nulls,
                column_default_val,
                column_length,
                column_scale,
                column_always_ident,
                column_bydefault_ident
            FROM
                iicolumns
            WHERE
                table_name = ?"""
        params = (self.denormalize_name(table_name),)

        if schema:
            sqltext += """
                AND table_owner = ?"""
            params = (*params, self.denormalize_name(schema))

        sqltext += """
            ORDER BY
                column_sequence"""

        rs = None
        columns = []
        try:
            rs = connection.exec_driver_sql(sqltext, params)

            for row in rs.fetchall():
                coldata = {}
                coldata["name"] = row[0].rstrip()
                coltype = row[1].rstrip()
                coldata["nullable"] = row[2].upper() == "Y"
                coldata["default"] = row[3]
                if (
                    coltype == "C"
                    or coltype == "CHAR"
                    or coltype == "VARCHAR"
                    or coltype == "TEXT"
                    or coltype == "NVARCHAR"
                    or coltype == "NCHAR"
                    or coltype == "BYTE"
                    or coltype == "BYTE VARYING"
                    or coltype == "FLOAT"
                ):
                    length = row[4]
                    coldata["type"] = ischema_names[coltype](length)
                elif coltype == "INTEGER":
                    length = row[4]
                    if length == 1:
                        coltype = "TINYINT"
                    elif length == 2:
                        coltype = "SMALLINT"
                    elif length == 4:
                        pass
                    elif length == 8:
                        coltype = "BIGINT"
                    else:
                        pass  # TODO review, unlikely to happen should this be trapped?
                    coldata["type"] = ischema_names[coltype]
                elif coltype == "DECIMAL":
                    (precision, scale) = (row[4], row[5])
                    coldata["type"] = ischema_names[coltype](precision, scale)
                else:
                    coldata["type"] = ischema_names[coltype]
                # Check values for column_always_ident, column_bydefault_ident
                coldata["autoincrement"] = row[6] == "Y" or row[7] == "Y"

                coldata["comment"] = self._get_column_comment(connection, table_name, coldata["name"], schema)

                columns.append(coldata)

            rs.close()
            return columns
        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_unique_constraints(self, connection, table_name, schema=None, **kw):
        sqltext = """
            SELECT
                k.constraint_name,
                k.column_name
            FROM
                iikeys k,
                iiconstraints c
            WHERE
                k.constraint_name = c.constraint_name
            AND c.constraint_type = 'U'
            AND k.table_name = ?"""
        params = (self.denormalize_name(table_name),)

        if schema:
            sqltext += """
                AND k.schema_name = ?"""
            params = (*params, self.denormalize_name(schema))

        rs = None

        try:
            rs = connection.exec_driver_sql(sqltext, params)

            constraints = []
            for row in rs.fetchall():
                constraint_name = row[0].rstrip()
                column_name = row[1].rstrip()

                constraint_exists_in_list = False
                for constraint_dict in constraints:
                    if constraint_name == constraint_dict["name"]:
                        constraint_dict["column_names"].insert(0, column_name)
                        constraint_exists_in_list = True

                if not constraint_exists_in_list:
                    constraint_dict = {
                        "name": constraint_name if constraint_name[0] != "$" else None,
                        "column_names": [column_name],
                    }
                    constraints.append(constraint_dict)

            return constraints

        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_primary_keys(self, connection, table_name, schema=None, **kw):
        sqltext = """
            SELECT
                k.column_name
            FROM
                iikeys k,
                iiconstraints c
            WHERE
                k.constraint_name = c.constraint_name
            AND c.constraint_type = 'P'
            AND k.table_name = ?"""
        params = (self.denormalize_name(table_name),)

        if schema:
            sqltext += """
                AND k.schema_name = ?"""
            params = (*params, self.denormalize_name(schema))

        rs = None

        try:
            rs = connection.exec_driver_sql(sqltext, params)

            cols = [row[0].rstrip() for row in rs.fetchall()]
            return {"constrained_columns": [] if cols is None else cols, "name": None}

        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        return self.get_primary_keys(connection, table_name, schema, **kw)

    @reflection.cache
    def get_foreign_keys(self, connection, table_name, schema=None, **kw):
        sqltext = """
            SELECT
                f.constraint_name AS name,
                f.column_name AS constrained_column,
                p.schema_name AS referred_schema,
                p.table_name AS referred_table,
                p.column_name AS referred_column
            FROM
                iikeys f,
                iikeys p,
                iiref_constraints rc,
                iiconstraints c
            WHERE
                c.constraint_type = 'R'
            AND c.constraint_name = rc.ref_constraint_name
            AND p.constraint_name = rc.unique_constraint_name
            AND f.constraint_name = rc.ref_constraint_name
            AND p.key_position = f.key_position
            AND f.table_name = ?"""
        params = (self.denormalize_name(table_name),)

        if schema:
            sqltext += """
                AND f.schema_name = ?"""
            params = (*params, self.denormalize_name(schema))

        sqltext += """
            ORDER BY
                f.key_position"""

        rs = None
        foreign_keys = {}
        try:
            rs = connection.exec_driver_sql(sqltext, params)

            for row in rs.fetchall():
                name = row[0].rstrip()
                if name in foreign_keys:
                    constraint = foreign_keys[name]
                else:
                    constraint = {}
                    constraint["name"] = name
                    constraint["constrained_columns"] = []
                    constraint["referred_table"] = row[3].rstrip()
                    constraint["referred_columns"] = []

                    ref_schema = row[2].rstrip()
                    def_schema = connection.dialect.default_schema_name

                    if def_schema != ref_schema:
                        constraint["referred_schema"] = ref_schema
                    else:
                        constraint["referred_schema"] = None
                    # constraint['referred_schema'] = row[2].rstrip()

                constraint["constrained_columns"].append(row[1].rstrip())
                constraint["referred_columns"].append(row[4].rstrip())

                foreign_keys[name] = constraint

            rs.close()
            return list(foreign_keys.values())
        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_table_names(self, connection, schema=None, **kw):
        sqltext = """
            SELECT
                table_name
            FROM
                iitables
            WHERE
                table_type = 'T'"""
        params = None

        if schema:
            sqltext += """
                AND table_owner = ?"""
            params = (self.denormalize_name(schema),)

            if schema != "$ingres":
                sqltext += " AND table_name NOT LIKE 'ii%'"
        else:
            sqltext += """
                AND table_owner != '$ingres'
                AND table_name NOT LIKE 'ii%'"""

        rs = None

        try:
            if params:
                rs = connection.exec_driver_sql(sqltext, params)
            else:
                # sqlalchemy assumes anything after query text is a list/tuple of values
                rs = connection.exec_driver_sql(sqltext)

            return [row[0].rstrip() for row in rs.fetchall()]
        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_schema_names(self, connection, **kw):
        sqltext = """
            SELECT
                schema_name
            FROM
                iischema"""

        rs = None

        try:
            rs = connection.exec_driver_sql(sqltext)

            return [row[0].rstrip() for row in rs.fetchall()]
        finally:
            if rs:
                rs.close()

    def table_names(self, connection, schema=None, **kw):
        return self.get_table_names(connection, schema, **kw)

    @reflection.cache
    def get_view_names(self, connection, schema=None, **kw):
        sqltext = """
            SELECT
                table_name
            FROM
                iiviews"""
        params = None

        if schema:
            sqltext += """
                WHERE
                    table_owner = ?"""
            params = (self.denormalize_name(schema),)
        else:
            sqltext += """
                WHERE
                    table_owner != '$ingres'"""

        rs = None

        try:
            if params:
                rs = connection.exec_driver_sql(sqltext, params)
            else:
                rs = connection.exec_driver_sql(sqltext)

            return [row[0].rstrip() for row in rs.fetchall()]
        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_view_definition(self, connection, view_name, schema=None, **kw):
        sqltext = """
            SELECT
                text_segment
            FROM
                iiviews
            WHERE
                table_name = ?"""
        params = (self.denormalize_name(view_name),)

        if schema:
            sqltext += """
                AND table_owner = ?"""
            params = (*params, self.denormalize_name(schema))
        else:
            sqltext += """
                AND table_owner != '$ingres'"""

        sqltext += """
            ORDER BY
                text_sequence"""

        rs = None

        try:
            rs = connection.exec_driver_sql(sqltext, params)

            return "".join([row[0] for row in rs.fetchall()])
        finally:
            if rs:
                rs.close()

    @reflection.cache
    def get_indexes(self, connection, table_name, schema=None, **kw):
        sqltext = """
            SELECT
                i.index_name,
                c.column_name,
                i.unique_rule
            FROM
                iiindexes i,
                iiindex_columns c
            WHERE
                i.index_name = c.index_name
            AND i.index_owner = c.index_owner
            AND i.base_name = ?"""
        params = (self.denormalize_name(table_name),)

        if (
            connection.get_execution_options().get("inspect_indexes") is None
            or connection.get_execution_options().get("inspect_indexes").upper() != "ALL"
        ):
            sqltext += """
                AND i.system_use = 'U'"""

        if schema:
            sqltext += """
                AND i.index_owner = ?"""
            params = (*params, self.denormalize_name(schema))

        sqltext += """
            ORDER BY
                c.key_sequence"""

        rs = None
        indexes = {}

        try:
            rs = connection.exec_driver_sql(sqltext, params)

            for row in rs.fetchall():
                name = row[0].rstrip()
                if name in indexes:
                    index = indexes[name]
                else:
                    index = {}
                    index["name"] = name
                    index["column_names"] = []
                    index["unique"] = row[2] == "U"

                index["column_names"].append(row[1].rstrip())

                indexes[name] = index

            return list(indexes.values())
        finally:
            if rs:
                rs.close()

    def normalize_name(self, name):
        if name is None:
            return None
        else:
            return name

    def denormalize_name(self, name):
        if name is None:
            return None
        else:
            return name

    def has_table(self, connection, table_name, schema=None, **kw):
        sqltext = """
            SELECT
                table_name
            FROM
                iitables
            WHERE
                table_name = ?
            AND table_type = 'T'"""
        params = (self.denormalize_name(table_name),)

        if schema:
            sqltext += """
                AND table_owner = ?"""
            params = (*params, self.denormalize_name(schema))

        rs = None
        try:
            rs = connection.exec_driver_sql(sqltext, params)
            return len(rs.fetchall()) > 0
        finally:
            if rs:
                rs.close()

    def has_sequence(self, connection, sequence_name, schema=None, **kw):
        sqltext = """
            SELECT
                seq_name
            FROM
                iisequences
            WHERE
                seq_name = ?"""
        params = (self.denormalize_name(sequence_name),)

        if schema:
            sqltext += """
                AND seq_owner = ?"""
            params = (*params, self.denormalize_name(schema))

        rs = None

        try:
            rs = connection.exec_driver_sql(sqltext, params)
            return len(rs.fetchall()) > 0
        finally:
            if rs:
                rs.close()

    def get_default_schema_name(self, connection):
        rs = None
        try:
            if sqlalchemy_version_tuple >= (2, 0):
                rs = connection.execute(func.dbmsinfo("username"))
            else:
                sqltext = """SELECT dbmsinfo('username')"""
                rs = connection.exec_driver_sql(sqltext)
            return rs.fetchone()[0]
        finally:
            if rs:
                rs.close()

    _get_default_schema_name = get_default_schema_name  # 1.4 API


def is_integer_greater_than_zero(check_value):
    return check_value is not None and check_value > 0
