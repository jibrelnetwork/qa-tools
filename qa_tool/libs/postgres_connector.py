import logging
import psycopg2
import psycopg2.extras
from qa_tool.libs.reporter import reporter


class PostgresConnector(object):
    SERIALIZE = psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
    AUTOCOMMIT = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT

    def __init__(self, host, user, password, database=None):  # Do we need support async there?
        port = None
        if ':' in host:
            host, port = host.rsplit(':', 1)
        self._connection_dict = {
            "host": host,
            "port": int(port) if port else port,
            "database": database,
            "user": user,
            "password": password,
        }
        self.driver = psycopg2

    def get_table_names(self):
        return [table["tablename"] for table in self.get("SELECT * FROM pg_catalog.pg_tables;")]

    def get(self, sql, as_dict=True, isolate_lvl=AUTOCOMMIT):
        # TODO: Maybe RealDictCursor -> NamedTupleCursor https://stackoverflow.com/questions/6739355/dictcursor-doesnt-seem-to-work-under-psycopg2
        cursor_factory = psycopg2.extras.RealDictCursor if as_dict else psycopg2.extras.DictCursor
        with reporter.step("Postgre SQL to host: {host}:{port}, db_name: {database}".format(**self._connection_dict)):
            msg = "SQL: %s" % sql
            logging.info(msg)
            print(msg)
            with self.driver.connect(**self._connection_dict) as conn:
                conn.set_isolation_level(isolate_lvl)
                cursor = conn.cursor(cursor_factory=cursor_factory)
                try:
                    cursor.execute(sql)
                    return cursor.fetchall()
                except (self.driver.ProgrammingError, self.driver.OperationalError) as e:
                    logging.error(e)
            reporter.attach('DB Query', msg)

    def insert(self, table_name, dict_to_insert, isolate_lvl=AUTOCOMMIT):
        """ WARNING! All strings passed unescaped """
        columns = []
        values = []
        for column, value in dict_to_insert.items():
            columns.append(column)
            values.append("'%s'" % value if isinstance(value, str) else str(value))
        query_data = {
            'columns': ', '.join(columns),
            'values': ', '.join(values),
            'table_name': table_name,
        }
        query = "INSERT INTO {table_name} ({columns}) VALUES ({values})".format(**query_data)
        return self.get(query, isolate_lvl=isolate_lvl)


if __name__ == "__main__":
    print(PostgresConnector('127.0.0.1:9432', 'jassets', 'postgres', 'jassets').get_table_names())
    print(PostgresConnector('127.0.0.1:9432', 'jassets', 'postgres', 'jassets').get('select * from assets;', isolate_lvl=PostgresConnector.SERIALIZE))
