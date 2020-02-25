from sshtunnel import SSHTunnelForwarder

from qa_tool.settings import SSH_PKEY_PATH, SSH_PKEY_PASSWORD

SSH_USERNAME = "jumper"
BASTION_PORT = 1022


def create_ssh_tunnel_for_service(bastion_cluster_name, remote_container_name, remote_target_port):
    """
    If some scope doesn't have bastion service, then you must wait 60 or more seconds
    Need wait this PR https://github.com/pahaz/sshtunnel/pull/156/commits
    """
    server = SSHTunnelForwarder(
        (bastion_cluster_name, BASTION_PORT),
        ssh_username=SSH_USERNAME,
        ssh_pkey=SSH_PKEY_PATH,
        ssh_private_key_password=SSH_PKEY_PASSWORD,
        remote_bind_address=(remote_container_name, remote_target_port)
    )
    server.start()
    return server.local_bind_port
