import os
import logging

from pathlib import Path

import psycopg2
import psycopg2.extras
from addict import Dict
from sh import pg_dump, pg_restore, psql

from qa_tool.libs.reporter import reporter
from qa_tool.utils.utils import generate_value

CURR_DIR = Path(__file__).parent


class PostgresConnector(object):
    SERIALIZE = psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
    AUTOCOMMIT = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT

    def __init__(self, host, user, password, database=None, port=None):  # Do we need support async there?
        if ':' in host and port is None:
            host, port = host.rsplit(':', 1)
        self._connection_dict = Dict({
            "host": host,
            "port": int(port if port else port),
            "database": database,
            "user": user,
            "password": password,
        })
        self.driver = psycopg2
        self.backup_db_path = CURR_DIR / f'backup_{self._connection_dict.database}_{generate_value()}.dump'

    def get_root_connection(self):
        if self._connection_dict.database == 'postgres':
            return self
        return PostgresConnector(**dict(self._connection_dict, database='postgres'))

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

    def _get_tool_args(self, db_name):
        _db_name = db_name or self._connection_dict.database
        if _db_name == 'postgres':
            raise Exception("Can't use postgres database for any backup/restore actions")
        return [
            '-h', self._connection_dict.host,
            '-p', self._connection_dict.port,
            '-U', self._connection_dict.user,
            '-d', _db_name
            ]

    def backup_db(self, db_name=None):
        os.environ['PGPASSWORD'] = self._connection_dict.password
        print(f'Start backup data for db {self._connection_dict.host}:{self._connection_dict.database}')
        with self.backup_db_path.open('wb') as f:
            pg_dump(*self._get_tool_args(db_name) + ['-Fc'], _out=f)
        print(f'Finish backup data for db {self._connection_dict.host}:{self._connection_dict.database}')
        return self.backup_db_path.is_file()

    def restore_db(self, db_name=None, restore_file_path=None, use_psql=False):
        os.environ['PGPASSWORD'] = self._connection_dict.password
        _path = restore_file_path or self.backup_db_path
        print('Start restore data')
        if use_psql:
            psql(*self._get_tool_args(db_name) + ['-f', str(_path)])
        else:
            pg_restore(*self._get_tool_args(db_name) + ['-c', str(_path)])
        print('finish restore data')

    # def drop_db(self):
    #     """
    #     https://dba.stackexchange.com/questions/11893/force-drop-db-while-others-may-be-connected
    #     """
    #     db_name = self._connection_dict.database
    #     root_connection = self.get_root_connection()
    #     root_connection.get(f"""
    #         UPDATE pg_database SET datallowconn = 'false' WHERE datname = '{db_name}';
    #         SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db_name}';
    #     """)
    #     root_connection.get(f"DROP DATABASE {db_name};")


if __name__ == "__main__":
    from qa_tool.static.infrastructure import InfraServiceType
    from qa_tool.libs.stacks import get_env_config

    dev_creds = get_env_config('jibrelcom', 'develop').get_service_connector(
        InfraServiceType.PGBOUNCER,
    )
    qa_creds = get_env_config('jibrelcom', 'qa').get_service_connector(
        InfraServiceType.PGBOUNCER,
    )
    dev_conn = PostgresConnector(**dev_creds, database='backend_main_db')
    qa_conn = PostgresConnector(**qa_creds, database='backend_main_db')
    dev_conn.backup_db()
    qa_conn.resotre_db(restore_file_path=str(dev_conn.backup_db_path))
    # print(test_conn.get_table_names())
    # test_conn.backup_db()
    # test_conn.drop_db()
    # qa_conn.drop_schema()
    # print(test_conn.get('select * from authentication_profile'))
    # print(PostgresConnector('127.0.0.1:9432', 'jassets', 'postgres', 'jassets').get_table_names())
    # print(PostgresConnector('127.0.0.1:9432', 'jassets', 'postgres', 'jassets').get('select * from assets;', isolate_lvl=PostgresConnector.SERIALIZE))
