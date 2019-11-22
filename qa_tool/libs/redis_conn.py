import json
import pickle
from redis import Redis

from qa_tool.libs.reporter import reporter


class RedisClient:

    def __init__(self, host, port=None, db=0):
        port = port or '6379'
        self.conn_str = f"{host}:{port}"
        self.redis = Redis(host=host, port=port, db=db)

    def keys(self):
        with reporter.step(f'Get all redis keys from {self.conn_str}'):
            keys = self.redis.keys()
            try:
                keys = [i.decode("UTF-8") for i in keys]
            finally:
                reporter.attach(f'Redis keys', keys)
                return keys

    def set(self, key, value, is_json=True):
        if is_json:
            data = json.dumps(value)
        else:
            data = pickle.dumps(value)
        self.redis.set(key, data)

    def get(self, key, is_json=True):
        with reporter.step(f'Get redis data by key {key} from {self.conn_str}'):
            data = self.redis.get(key)
            try:
                if is_json:
                    data = json.loads(data)
                else:
                    data = pickle.loads(data)
            finally:
                reporter.attach(f'Redis data by {key}', data)
                return data

    def get_redis_dict(self):
        raise NotImplementedError # TODO: implement this with yield data logic from key in dict
        return


if __name__ == '__main__':
    host, port = 'localhost:25550'.rsplit(':', 1)
    r = Redis(host=host, port=port, db=0)
    print('test')