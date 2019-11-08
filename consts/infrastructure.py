from qa_tool.custom_structure import Enum

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
    DEV = 'Develop'
    STAGE = 'Stage'
    PROD = 'Production'
    ALL = 'All'

    ENV_BY_ALIAS = {al: env for env, aliases in {
        DEV: ['dev', 'develop'],
        STAGE: ['stage'],
        PROD: ['prod', 'production'],
    }.items() for al in aliases}

    @classmethod
    def get_env_by_alias(cls, env: str):
        return cls._ALIASES_BY_ENV.get(env.lower())


class ServiceScope(InfrastructureUtil):
    JTICKER = 'JTicker'
    JSEARCH = 'JSearch'
    COINMENA = 'Coinmena'





