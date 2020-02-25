from qa_tool.libs.reporter import reporter
from qa_tool.libs.stacks import get_env_config, bastion_connection_config
from qa_tool.libs.influx_connector import InfluxConnector
from qa_tool.libs.postgres_connector import PostgresConnector
from consts.infrastructure import ServiceScope, Environment, InfraServiceType


class TestSSHConnector:

    def _check_access_to_scope(self, service_scope, service_type):
        self.env_observer = get_env_config(service_scope, Environment.DEV)
        return self.env_observer.get_service_connector(service_type)

    def test_connection_dont_close_after_open_and_check_config_saver(self):
        observer = get_env_config(ServiceScope.JTICKER, Environment.DEV)
        with bastion_connection_config(observer.bastion_cluster_url) as config:
            service = [i for i in observer.services if i.container_image_name == InfraServiceType.PGBOUNCER]
            assert len(service) == 1
            assert not config.get(service[0].container_name)
        conn_params = dict(self._check_access_to_scope(ServiceScope.JTICKER, InfraServiceType.PGBOUNCER))
        assert conn_params == self._check_access_to_scope(ServiceScope.JTICKER, InfraServiceType.PGBOUNCER)

    def test_connect_to_jticker_influx(self):
        conn_params = self._check_access_to_scope(ServiceScope.JTICKER, InfraServiceType.INFLUX_DB)
        connector = InfluxConnector(**conn_params, database='test')
        tables = connector.get_tables_name()
        assert tables
        data = connector.get('select * from mapping', arrg_data=False)
        assert data

    def test_connect_to_postgres_coinmena(self):
        conn_params = self._check_access_to_scope(ServiceScope.COINMENA, InfraServiceType.PGBOUNCER)
        conn = PostgresConnector(**conn_params, database='coinmena_main')
        tables = conn.get_table_names()
        assert tables
        data = conn.get("SELECT * FROM core_assets_assetpair")
        assert data

    def test_connect_to_postgres_jibrelcom(self):
        conn_params = self._check_access_to_scope(ServiceScope.JIBRELCOM, InfraServiceType.PGBOUNCER)
        conn = PostgresConnector(**conn_params, database='jibrelcom_db')
        tables = conn.get_table_names()
        assert tables
        data = conn.get("SELECT * FROM core_assets_assetpair")
        assert data


if __name__ == '__main__':
    from qa_tool import run_test
    run_test(__file__)
