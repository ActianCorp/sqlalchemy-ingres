from sqlalchemy.testing.requirements import SuiteRequirements

from sqlalchemy.testing import exclusions

class Requirements(SuiteRequirements):
    @property
    def date_historic(self):
        """target dialect supports representation of Python
        datetime.datetime() objects with historic (pre 1970) values."""
        return exclusions.open()

    @property
    def datetime_historic(self):
        """target dialect supports representation of Python
        datetime.datetime() objects with historic (pre 1970) values."""
        return exclusions.open()

    @property
    def datetime_literals(self):
        """target dialect supports rendering of a date, time, or datetime as a
        literal string, e.g. via the TypeEngine.literal_processor() method.

        """
        return exclusions.open()

    @property
    def identity_columns(self):
        """If a backend supports GENERATED { ALWAYS | BY DEFAULT }
        AS IDENTITY"""
        return exclusions.open()

    @property
    def identity_columns_standard(self):
        """If a backend supports GENERATED { ALWAYS | BY DEFAULT }
        AS IDENTITY with a standard syntax.
        This is mainly to exclude MSSql.
        """
        return exclusions.open()

