from collections import OrderedDict

from qa_tool.custom_structure import Enum
from qa_tool.utils.utils import classproperty

DOCKER_REGISTRY_ORG = "jibrelnetwork"
WARNING_BRANCHES = ['master', ]


class InfrastructureUtil(Enum):

    @classmethod
    def find(cls, msg: str):
        msg = msg.lower()
        for i in cls.get_all():
            if i.lower() in msg:
                return i


class Environment(InfrastructureUtil):
    DEV = 'develop'
    STAGE = 'stage'
    PROD = 'production'
    QA = 'qa'

    @classproperty
    def ALL(self):
        return 'all'

    @classproperty
    def LOCAL(self):
        return 'local'

    __env_alias = None
    @classproperty
    def ENV_BY_ALIAS(cls):
        if cls.__env_alias is None:
            cls.__env_alias = OrderedDict(sorted([(al, env) for env, aliases in {
                cls.DEV: ['dev', 'develop'],
                cls.STAGE: ['stage'],
                cls.PROD: ['prod', 'production'],
            }.items() for al in aliases], key=lambda k_v_pair: len(k_v_pair[0]), reverse=True))
        return cls.__env_alias

    @classmethod
    def get_env_by_alias(cls, env: str):
        return cls.ENV_BY_ALIAS.get(env.lower())


class ServiceScope(InfrastructureUtil):
    JNA = 'jna'
    JIBRELCOM = 'jibrelcom'
    JTICKER = 'jticker'
    JSEARCH = 'jsearch'
    COINMENA = 'coinmena'

    @classproperty
    def ALL(self):
        return 'all'


class InfraServiceType:
    PGBOUNCER = 'pgbouncer'
    INFLUX_DB = 'influxdb'
    KAFKA = 'kafka'
    REDIS = 'redis'
    ADMIN = 'admin'
    CMS = 'default'
