import json
from kafka import KafkaProducer

from qa_tool.libs.reporter import reporter


class KafkaManager:

    def __init__(self, kafka_uri, map_timeout=5, serialize_data=True, **kwargs):
        with reporter.step(f'Connect to kafka: {kafka_uri}'):
            if serialize_data:
                _serialize_fn = lambda v: json.dumps(v).encode('utf-8')
                kwargs['value_serializer'] = _serialize_fn
                kwargs['key_serializer'] = _serialize_fn
            self.producer = KafkaProducer(bootstrap_servers=kafka_uri, **kwargs)
            self.timeout = map_timeout

    def send(self, topic, data, key=None, get_result=True, **kwargs):
        with reporter.step(f'Send data to topic: {topic}'):
            reporter.attach(f'Sending data', data)
            future = self.producer.send(topic, data, key=key, **kwargs)
            if get_result:
                response = future.get(self.timeout)
                reporter.attach(f'Added topic data', response)
                assert future.is_done
            return future
