from django.db.models.sql import compiler


class SQLCompiler(compiler.SQLCompiler):
    def resolve_columns(self, row, fields=()):
        # If this query has limit/offset information, then we expect the
        # first column to be an extra "_RN" column that we need to throw
        # away.
        rn_offset = 1 if self.query.high_mark is not None or self.query.low_mark else 0
        index_start = rn_offset + len(self.query.extra_select.keys())
        values = [self.query.convert_values(v, None, connection=self.connection)
                  for v in row[rn_offset:index_start]]
        values.extend(
            self.query.convert_values(value, field, connection=self.connection)
            for value, field in map(None, row[index_start:], fields)
        )
        return tuple(values)

    def as_sql(self, with_limits=True, with_col_aliases=False):
        """
        Creates the SQL for this query. Returns the SQL string and list
        of parameters.  This is overriden from the original Query class
        to handle the additional SQL Oracle requires to emulate LIMIT
        and OFFSET.

        If 'with_limits' is False, any limit/offset information is not
        included in the query.
        """
        if with_limits and self.query.low_mark == self.query.high_mark:
            return '', ()

        if do_offset := with_limits and (
            self.query.high_mark is not None or self.query.low_mark
        ):
            sql, params = super(SQLCompiler, self).as_sql(with_limits=False,
                                                    with_col_aliases=True)

            high_where = (
                'WHERE ROWNUM <= %d' % (self.query.high_mark,)
                if self.query.high_mark is not None
                else ''
            )
            sql = 'SELECT * FROM (SELECT ROWNUM AS "_RN", "_SUB".* FROM (%s) "_SUB" %s) WHERE "_RN" > %d' % (sql, high_where, self.query.low_mark)

        else:
            sql, params = super(SQLCompiler, self).as_sql(with_limits=False,
                    with_col_aliases=with_col_aliases)
        return sql, params


class SQLInsertCompiler(compiler.SQLInsertCompiler, SQLCompiler):
    pass

class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    pass

class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    pass

class SQLAggregateCompiler(compiler.SQLAggregateCompiler, SQLCompiler):
    pass

class SQLDateCompiler(compiler.SQLDateCompiler, SQLCompiler):
    pass
