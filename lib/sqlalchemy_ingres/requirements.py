from sqlalchemy.testing.requirements import SuiteRequirements

from sqlalchemy.testing import exclusions
from sqlalchemy.testing.exclusions import against
from sqlalchemy.testing.exclusions import only_on
from sqlalchemy.testing.exclusions import fails_on_everything_except

supported = exclusions.open
unsupported = exclusions.closed

class Requirements(SuiteRequirements):
    @property
    def date_historic(self):
        """target dialect supports representation of Python
        datetime.datetime() objects with historic (pre 1970) values."""
        return supported()

    @property
    def datetime_historic(self):
        """target dialect supports representation of Python
        datetime.datetime() objects with historic (pre 1970) values."""
        return supported()

    @property
    def datetime_literals(self):
        """target dialect supports rendering of a date, time, or datetime as a
        literal string, e.g. via the TypeEngine.literal_processor() method.

        """
        return supported()

    @property
    def identity_columns(self):
        """If a backend supports GENERATED { ALWAYS | BY DEFAULT }
        AS IDENTITY"""
        return supported()

    @property
    def identity_columns_standard(self):
        """If a backend supports GENERATED { ALWAYS | BY DEFAULT }
        AS IDENTITY with a standard syntax.
        This is mainly to exclude MSSql.
        """
        return supported()

    @property
    def array_type(self):
        return supported()

    @property
    def unique_constraint_reflection(self):
        return supported()

    @property
    def temp_table_reflection(self):
        return unsupported()


