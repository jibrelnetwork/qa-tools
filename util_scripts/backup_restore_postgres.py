import os
from distutils.util import strtobool

from qa_tool.settings import ENV_SERVICE_SCOPE_NAME
from qa_tool.libs.reporter import reporter
from qa_tool.libs.stacks import get_env_config
from qa_tool.libs.postgres_connector import PostgresConnector
from qa_tool.static.infrastructure import Environment, InfraServiceType


RESTORE_ENVIRONMENT = strtobool(os.getenv('RESTORE_ENVIRONMENT', False))
BACKUP_ENV_NAME = os.getenv('BACKUP_ENV_NAME', Environment.DEV)
_RESTORE_ENV_NAME = Environment.QA
DATABASES_FOR_RESTORE = os.getenv('DATABASES_FOR_RESTORE', '')  # like:'db1,db2'


@reporter.scenario
class TestBackupRestorePostgres:

    def setup_class(self):
        self.dev_creds = get_env_config(ENV_SERVICE_SCOPE_NAME, BACKUP_ENV_NAME).get_service_connector(
            InfraServiceType.PGBOUNCER,
        )
        self.qa_creds = get_env_config(ENV_SERVICE_SCOPE_NAME, _RESTORE_ENV_NAME).get_service_connector(
            InfraServiceType.PGBOUNCER,
        )

    def test_prepare_image_env_data(self):
        if not RESTORE_ENVIRONMENT:
            reporter.skip_test(f"Don't need restore DBs: {DATABASES_FOR_RESTORE}")

        for db_name in [i.replace(' ', '') for i in DATABASES_FOR_RESTORE.split(',')]:
            backup_conn = PostgresConnector(**self.dev_creds, database=db_name)
            restore_conn = PostgresConnector(**self.qa_creds, database=db_name)
            with reporter.step("Backup data"):
                backup_conn.backup_db()
            with reporter.step("Restore data"):
                restore_conn.restore_db(restore_file_path=str(self.backup_conn.backup_db_path))


if __name__ == "__main__":
    from qa_tool import run_test
    run_test(__file__)
