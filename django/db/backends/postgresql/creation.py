from django.db.backends.creation import BaseDatabaseCreation
from django.db.backends.util import truncate_name

class DatabaseCreation(BaseDatabaseCreation):
    # This dictionary maps Field objects to their associated PostgreSQL column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__ before being output.
    # If a column type is set to None, it won't be included in the output.
    data_types = {
        'AutoField':         'serial',
        'BooleanField':      'boolean',
        'CharField':         'varchar(%(max_length)s)',
        'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
        'DateField':         'date',
        'DateTimeField':     'timestamp with time zone',
        'DecimalField':      'numeric(%(max_digits)s, %(decimal_places)s)',
        'FileField':         'varchar(%(max_length)s)',
        'FilePathField':     'varchar(%(max_length)s)',
        'FloatField':        'double precision',
        'IntegerField':      'integer',
        'BigIntegerField':   'bigint',
        'IPAddressField':    'inet',
        'NullBooleanField':  'boolean',
        'OneToOneField':     'integer',
        'PositiveIntegerField': 'integer CHECK ("%(column)s" >= 0)',
        'PositiveSmallIntegerField': 'smallint CHECK ("%(column)s" >= 0)',
        'SlugField':         'varchar(%(max_length)s)',
        'SmallIntegerField': 'smallint',
        'TextField':         'text',
        'TimeField':         'time',
    }

    def sql_table_creation_suffix(self):
        assert self.connection.settings_dict['TEST_COLLATION'] is None, "PostgreSQL does not support collation setting at database creation time."
        if self.connection.settings_dict['TEST_CHARSET']:
            return f"WITH ENCODING '{self.connection.settings_dict['TEST_CHARSET']}'"
        return ''

    def sql_indexes_for_field(self, model, f, style):
        if f.db_index and not f.unique:
            qn = self.connection.ops.quote_name
            db_table = model._meta.db_table
            tablespace = f.db_tablespace or model._meta.db_tablespace
            if tablespace:
                sql = self.connection.ops.tablespace_sql(tablespace)
                tablespace_sql = f' {sql}' if sql else ''
            else:
                tablespace_sql = ''

            def get_index_sql(index_name, opclass=''):
                return (
                    style.SQL_KEYWORD('CREATE INDEX')
                    + ' '
                    + style.SQL_TABLE(
                        qn(
                            truncate_name(
                                index_name, self.connection.ops.max_name_length()
                            )
                        )
                    )
                    + ' '
                    + style.SQL_KEYWORD('ON')
                    + ' '
                    + style.SQL_TABLE(qn(db_table))
                    + ' '
                    + f"({style.SQL_FIELD(qn(f.column))}{opclass})"
                ) + f"{tablespace_sql};"

            output = [get_index_sql(f'{db_table}_{f.column}')]

            # Fields with database column types of `varchar` and `text` need
            # a second index that specifies their operator class, which is
            # needed when performing correct LIKE queries outside the
            # C locale. See #12234.
            db_type = f.db_type(connection=self.connection)
            if db_type.startswith('varchar'):
                output.append(
                    get_index_sql(
                        f'{db_table}_{f.column}_like', ' varchar_pattern_ops'
                    )
                )
            elif db_type.startswith('text'):
                output.append(
                    get_index_sql(
                        f'{db_table}_{f.column}_like', ' text_pattern_ops'
                    )
                )
        else:
            output = []
        return output
