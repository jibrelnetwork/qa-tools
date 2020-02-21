import json
import socket
from contextlib import contextmanager

from addict import Dict
from pathlib import Path
from sshtunnel import SSHTunnelForwarder
import psycopg2

from qa_tool.settings import SSH_PKEY_PATH

SSH_USERNAME = "jumper"
BASTION_PORT = 1022

CURR_DIR = Path('/app').resolve() if Path('/app').is_dir() else Path(__file__).parent
BASTION_CONFIG_FILE_PATH = CURR_DIR / 'bastion_connectors_cfg.json'


class BastionCfgVariable:
    PORT = 'local_port'
    USER = 'local_port'
    PASSWORD = 'local_port'

# cluster_name = "jticker.develop.jdev.network"
# cluster_name = "jibrelcom.develop.jdev.network"
# cluster_name = "coinmena.develop.coinmena.dev"


# remote_target_name = "jticker_develop_pgbouncer"  # container name
# remote_target_name = "coinmena_develop_pgbouncer"  # container name
# remote_target_port = 5432


# server = SSHTunnelForwarder(
#     (cluster_name, BASTION_PORT),
#     ssh_username=SSH_USERNAME,
#     ssh_pkey=SSH_PKEY_PATH,
#     remote_bind_address=(remote_target_name, remote_target_port)
# )
#
# server.start()
#
# local_port = server.local_bind_port
#
# print(local_port)
# conn = psycopg2.connect(host='localhost',
#                         dbname="postgres",
#                         user="postgres",
#                         port=server.local_bind_port,
#                         # password="KxfnqRbC74s6tbXL")
#                         password="coinmena_develop_postgres_pass")
#
# cur = conn.cursor()
# cur.execute('SELECT * FROM pg_database;')
# rows = cur.fetchall()
# for row in rows:
#     print(row)
# cur.close()
#
# conn.close()
#
#
# server.stop()


@contextmanager
def bastion_connection_config(bastion_cluster_name):
    try:
        config = Dict(json.loads(BASTION_CONFIG_FILE_PATH.read_text()))
    except Exception as e:
        config = Dict({bastion_cluster_name: {}})

    yield config

    BASTION_CONFIG_FILE_PATH.write_text(json.dumps(config))


def check_socket_is_busy(port):
    if port is None:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def create_ssh_tunnel_for_service(bastion_cluster_name, remote_container_name, remote_target_port):
    with bastion_connection_config(bastion_cluster_name) as config:
        interested_port = config.get(remote_container_name, {}).get(BastionCfgVariable.PORT)

        if check_socket_is_busy(interested_port):
            return interested_port

        server = SSHTunnelForwarder(
            (bastion_cluster_name, BASTION_PORT),
            ssh_username=SSH_USERNAME,
            ssh_pkey=SSH_PKEY_PATH,
            remote_bind_address=(remote_container_name, remote_target_port)
        )
        server.start()
        port = server.local_bind_port
        config[remote_container_name][BastionCfgVariable.PORT] = port
    return config[remote_container_name]


if __name__ == '__main__':
    print(check_socket_is_busy(9091))
    print(check_socket_is_busy(9092))
    print(check_socket_is_busy(9093))
