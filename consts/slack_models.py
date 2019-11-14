import time
from collections import namedtuple, defaultdict

from addict import Dict
from marshmallow import fields, Schema, post_load, pre_dump

EnvInfo = namedtuple('EnvInfo', ['scope', 'env', 'id', 'name'])


class SetField(fields.Field):

    def _serialize(self, value, attr, obj, **kwargs):
        return list(value)

    def _deserialize(self, value, attr, data, **kwargs):
        return set(value)


class _EnvInfo(fields.Field):
    _separator = '__'

    def _serialize(self, value, attr, obj, **kwargs):
        return self._separator.join(str(i) for i in value)

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, EnvInfo):
            return value
        return EnvInfo(*value.split(self._separator))


class _EnvironmentServices(Schema):
    services = fields.Dict(keys=fields.Str(), values=SetField())
    previous_services = fields.Dict(keys=fields.Str(), values=SetField())
    last_update = fields.Float(default=time.time())
    last_service_update = fields.Float(default=time.time())
    last_previous_service_update = fields.Float(default=time.time())


class EnvironmentConfig(Schema):
    all_env_conf = fields.Dict(keys=_EnvInfo(), values=fields.Nested(_EnvironmentServices))

    @pre_dump
    def wrap_with_envelope(self, data, many, **kwargs):
        return {'all_env_conf': data}

    @post_load
    def to_default_dict(self, in_data, **kwargs):
        in_data = in_data['all_env_conf']
        for k, v in in_data.items():
            v["services"] = defaultdict(set, v["services"])
            v["previous_services"] = defaultdict(set, v["previous_services"])
        return Dict(in_data)


class SubscribersConfig(Schema):
    subs_by_env = fields.Dict(keys=_EnvInfo(), values=SetField())

    @pre_dump
    def wrap_with_envelope(self, data, many, **kwargs):
        return {'subs_by_env': data}

    @post_load
    def to_default_dict(self, in_data, **kwargs):
        return in_data['subs_by_env']


if __name__ == '__main__':
    env_conf = """{"all_env_conf": {
        "123__123__qwe2__name1": {
            "services": {"qweqw": [1, 2, 3]},
            "previous_services": {"qweqw": [1, 2, 3]},
            "last_update": 123.123,
            "last_service_update": 333.3,
            "last_previous_service_update": 123213.32
        }
    }}"""

    subs = EnvironmentConfig()
    keks = subs.loads(env_conf)
    assert isinstance(keks[EnvInfo('123', '123', 'qwe2', 'name1')]['services']['qweqw'], set)
    subs.dump(keks)
    subs.dumps(keks)
    print('123')

    # many_subs = {'subs_by_env': {
    #     '123__123__qwe__name': [1, 2, 3, 3],
    #     # EnvInfo('123', '123', 'qwe', 'name'): ['qwe', 'qwe'],
    #     EnvInfo('123', '123', 'qwe2', 'name1'): ['qwe', 'qwe', 123],
    # }}
    #
    # subs = SubscribersConfig()
    # keks = subs.load(many_subs)
    #
    # print('123')
