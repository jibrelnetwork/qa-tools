import json
from redis import Redis

from qa_tool.libs.reporter import reporter


class RedisClient:

    def __init__(self, host, port, db=0):
        self.conn_str = f"{host}:{port}"
        self.redis = Redis(host=host, port=port, db=db)

    def keys(self):
        with reporter.step(f'Get all redis keys from {self.conn_str}'):
            keys = self.redis.keys()
            try:
                keys = [str(i) for i in keys]
            finally:
                reporter.attach(f'Redis keys', keys)
                return keys

    def get(self, key):
        with reporter.step(f'Get redis data by key {key} from {self.conn_str}'):
            data = self.redis.get(key)
            try:
                data = json.loads(data)
            finally:
                reporter.attach(f'Redis data by {key}', data)
                return data


if __name__ == '__main__':
    host, port = 'localhost:25550'.rsplit(':', 1)
    r = Redis(host=host, port=port, db=0)
    print('test')