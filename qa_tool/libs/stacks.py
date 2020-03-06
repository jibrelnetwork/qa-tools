import json
import socket
from typing import List
from dataclasses import dataclass
from contextlib import contextmanager

from addict import Dict
from pathlib import Path
from cachetools.func import lru_cache
from cached_property import cached_property

from qa_tool.settings import ENV_NAME, ENV_SERVICE_SCOPE_NAME
from qa_tool.libs.ssh_tunel import create_ssh_tunnel_for_service
from libs.portainer_conn import get_service_credentials_from_portainer
from qa_tool.static.infrastructure import ServiceScope, Environment, InfraServiceType


CURR_DIR = Path('/app').resolve() if Path('/app').is_dir() else Path(__file__).parent
BASTION_CONFIG_FILE_PATH = CURR_DIR / 'bastion_connectors_cfg.json'

DEFAULT_PORT_BY_SERVICE = {
    InfraServiceType.PGBOUNCER: 5432,
    InfraServiceType.INFLUX_DB: 8086,
    InfraServiceType.KAFKA: 9092,
}


class BastionCfgVariable:
    PORT = 'local_port'
    USER = 'local_port'
    PASSWORD = 'local_port'


def is_local_environment():
    return Environment.LOCAL == ENV_NAME


def is_port_in_use(port):
    if not port:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


@contextmanager
def bastion_connection_config(bastion_cluster_name):
    try:
        config = Dict(json.loads(BASTION_CONFIG_FILE_PATH.read_text()))
    except Exception as e:
        config = Dict({bastion_cluster_name: {}})

    yield config[bastion_cluster_name]

    BASTION_CONFIG_FILE_PATH.write_text(json.dumps(config))


@dataclass
class EnvService:
    # coinmena postgres dev (pgbouncer, POSTGRES_USER, POSTGRES_PASSWORD, ADMIN_DB_PORT)
    container_image_name: str
    login_variable: str = None
    password_variable: str = None
    need_create_connection: bool = True
    container_suffix: str = ''  # use if has more than one infra service (like two pgbouncer in jsearch)
    __env_observer = None

    def get_user_password(self):
        with bastion_connection_config(self.env_observer.bastion_cluster_url) as services_config:
            container_config = services_config.get(self.container_name, {})
            user = container_config.get('user')
            password = container_config.get('password')
            if not password and self.password_variable:
                user, password = get_service_credentials_from_portainer(
                    self.env_observer.scope_name, self.env_observer.env, self.container_name, self.login_variable,
                    self.password_variable
                )
            result = {"user": user, "password": password}
            services_config.update({self.container_name: result})
            return result

    def get_connection_params(self):
        port = DEFAULT_PORT_BY_SERVICE.get(self.container_image_name, 8080)
        with bastion_connection_config(self.env_observer.bastion_cluster_url) as services_config:
            container_config = services_config.get(self.container_name, {})
            interested_port = container_config.get('port', None)

            if is_port_in_use(interested_port):
                port = interested_port
            else:
                if self.need_create_connection:
                    port = self.create_connection(port)
            user_password = self.get_user_password()
            result = dict(user_password, port=port)
            services_config.update({self.container_name: result})
            return result

    def create_connection(self, default_port):
        if is_local_environment():
            raise Exception('You use local environment. Check ENV_NAME sys variable')
        return create_ssh_tunnel_for_service(self.env_observer.bastion_cluster_url, self.container_name, default_port)

    @property
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


class EnvObserver:

    def __init__(self, scope_name: str, env: str, services: List[EnvService]):
        self.scope_name = scope_name
        self.env = env
        self.services = services
        for i in services:
            i.env_observer = self

    @cached_property
    def bastion_cluster_url(self):
        bastion_url_suffix = 'coinmena.dev' if self.scope_name == ServiceScope.COINMENA else 'jdev.network'
        return '.'.join([self.scope_name, self.env, bastion_url_suffix]).lower()

    def get_host_url(self, domain_prefix=None, protocol='https://', host_for_local_env=None):
        if is_local_environment():
            return host_for_local_env
        host = self.bastion_cluster_url
        if domain_prefix:
            host = f'{domain_prefix}.{host}'
        return protocol + host

    def get_interested_service(self, infra_service_type: InfraServiceType, specify_container_name=''):
        services = [
            i for i in self.services
            if i.container_image_name == infra_service_type
               and not (specify_container_name)
               and i.container_suffix == specify_container_name
        ]
        assert len(services) == 1, "Need specify connection, because this scope has two or more same infrastructure service"
        return services[0]

    def get_service_creds(self, infra_service_type: InfraServiceType, specify_container_name='', connector_map=None):
        if is_local_environment():
            assert connector_map
            return connector_map
        service = self.get_interested_service(infra_service_type, specify_container_name)
        return service.get_user_password()

    def get_service_connector(self, infra_service_type: InfraServiceType, specify_container_name='', connector_map=None):
        if is_local_environment():
            assert connector_map
            return connector_map

        service = self.get_interested_service(infra_service_type, specify_container_name)
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


@lru_cache()
def get_env_config(service_scope=ENV_SERVICE_SCOPE_NAME, env_name=ENV_NAME) -> EnvObserver:
    if not service_scope:
        raise Exception(
            f"Set service scope in env variable 'ENV_SERVICE_SCOPE_NAME'\n One of this: {ServiceScope.get_all()}"
        )

    return EnvObserver(service_scope, env_name, ENVIRONMENTS_SERVICES[service_scope])


if __name__ == '__main__':
    print(get_env_config('jibrelcom').get_host_url())
    print(get_env_config('jibrelcom').get_host_url('api'))
    print(get_env_config('jibrelcom').get_host_url('qa'))
    # keks = EnvObserver(ServiceScope.JIBRELCOM, Environment.QA, ENVIRONMENTS_SERVICES[ServiceScope.JIBRELCOM])
    # lol = keks.get_service_connector(InfraServiceType.PGBOUNCER)
    # print(lol)
