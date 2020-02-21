from dataclasses import dataclass
from typing import List

from cached_property import cached_property

from qa_tool.libs.ssh_tunel import create_ssh_tunnel_for_service
from qa_tool.settings import ENV_NAME, ENV_SERVICE_SCOPE_NAME
from consts.infrastructure import ServiceScope, Environment, InfraServiceType


def is_local_environment():
    return Environment.LOCAL == ENV_NAME


DEFAULT_PORT_BY_SERVICE = {
    InfraServiceType.PGBOUNCER: 5432,
    InfraServiceType.INFLUX_DB: 8086,
    InfraServiceType.KAFKA: 9092,
}


@dataclass
class EnvService:
    # coinmena postgres dev (pgbouncer, POSTGRES_USER, POSTGRES_PASSWORD, ADMIN_DB_PORT)
    container_image_name: str
    login_variable: str = None
    password_variable: str = None
    need_create_connection: bool = True
    container_suffix: str = ''  # use if has more than one infra service (like two pgbouncer in jsearch)
    __env_observer = None

    def get_connection_params(self):
        port = DEFAULT_PORT_BY_SERVICE.get(self.container_image_name, 8080)
        if self.need_create_connection:
            port = self.create_connection(port)
        user, password = get_service_credentials_from_portainer(
            self.container_name, self.login_variable, self.password_variable
        )
        return {
            'user': user,
            'password': password,
            'port': port,
        }

    def create_connection(self, default_port):
        if is_local_environment():
            raise Exception('You use local environment. Check ENV_NAME sys variable')
        return create_ssh_tunnel_for_service(self.env_observer.bastion_cluster_url, self.container_name, default_port)

    @cached_property
    def container_name(self):
        name = '_'.join([self.env_observer.scope_name, self.env_observer.env, self.container_image_name]).lower()
        if self.container_suffix:
            name += f"-{self.container_suffix}"
        return name

    @property
    def env_observer(self):
        return self.__env_observer

    @env_observer.setter
    def env_observer(self, env_observer):
        self.__env_observer = env_observer


@dataclass
class EnvObserver:
    scope_name: str
    env: str
    services: List[EnvService]
    bastion_url_suffix: str = 'jdev.network'

    @cached_property
    def bastion_cluster_url(self):
        return '.'.join([self.scope_name, self.env, self.bastion_url_suffix]).lower()

    def get_service_connector(self, infra_service_type: InfraServiceType, specify_container_name='', connector_map=None):
        if is_local_environment():
            assert connector_map
            return connector_map

        services = [
            i for i in self.services
            if i.container_image_name == infra_service_type
               and not(specify_container_name)
               and i.container_suffix == specify_container_name
        ]
        assert len(services) == 1, "Need specify connection, because this scope has two or more same infrastructure service"
        service = services[0]
        service.env_observer = self

        result_data = service.get_connection_params()
        result_data['host'] = 'localhost'
        return result_data


def pgbouncer_service(container_suffix=''):
    return EnvService(InfraServiceType.PGBOUNCER, 'POSTGRES_USER', 'POSTGRES_PASSWORD', container_suffix=container_suffix)


def django_admin_service():
    return EnvService(InfraServiceType.ADMIN, '', 'ADMIN_PASSWORD')


ENVIRONMENTS_SERVICES = {
    ServiceScope.COINMENA: [pgbouncer_service(), django_admin_service()],
    ServiceScope.JIBRELCOM: [pgbouncer_service(), django_admin_service()],
    ServiceScope.JSEARCH: [pgbouncer_service('main'), pgbouncer_service('contracts')],
    ServiceScope.JTICKER: [pgbouncer_service(), EnvService(InfraServiceType.INFLUX_DB)],
}

EnvObserver(ENV_SERVICE_SCOPE_NAME, ENV_NAME, ENVIRONMENTS_SERVICES[ENV_SERVICE_SCOPE_NAME])
