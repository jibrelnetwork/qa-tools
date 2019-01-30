from os import path
import json
import requests


class Node():
    def __init__(self, url):
        self.url = url
        self.json_header = {"jsonrpc": "2.0", "id": 777}

    def _get_data(self, payload):
        response = requests.post(self.url, json=payload)
        result = json.loads(response.text)
        return result["result"]

    def block_by_number(self, number):
        payload = {
            "method": "eth_getBlockByNumber",
            "params": [hex(number), False]
        }
        payload.update(self.json_header)
        return self._get_data(payload)

    def block_by_hash(self, block_hash):
        payload = {
            "method": "eth_getBlockByHash",
            "params": [block_hash, False]
        }
        payload.update(self.json_header)
        return self._get_data(payload)

    def block_transactions(self, block_number):
        payload = {
            "method": "eth_getBlockByNumber",
            "params": [hex(block_number), True]
        }
        payload.update(self.json_header)

        return self._get_data(payload)["transactions"]

    def block_uncles(self, block_number):
        payload = {
            "method": "eth_getUncleCountByBlockNumber",
            "params": [hex(block_number)]
        }
        payload.update(self.json_header)
        uncle_count = int(self._get_data(payload), 16)

        payload = {
            "method": "eth_getUncleByBlockNumberAndIndex"
        }
        payload.update(self.json_header)

        uncle_list = []
        for idx in range(uncle_count):
            payload.update({"params": [hex(block_number), hex(idx)]})
            uncle_list.append(self._get_data(payload))

        result = sorted(uncle_list, key=lambda x: x['hash'])

        return result


class JsearchToRpcDataConverter():
    def __init__(self):
        pass

    @staticmethod
    def _convert(numeric, data):
        for key in numeric:
            data[key] = hex(data[key])
        return data

    def block(self, block):
        numeric = [
            "difficulty",
            "gasLimit",
            "gasUsed",
            "number",
            # "size", # FIXME Blocked by SEARCH-140 !! Incorrect `null` value broke self._convert method
            "timestamp",
            # "totalDifficulty", # FIXME Blocked by SEARCH-140!!
        ]
        return self._convert(numeric, block)

    def transaction(self, transaction):
        numeric = [
            "blockNumber",
            "transactionIndex",
        ]
        return self._convert(numeric, transaction)

    def uncle(self, uncle):
        numeric = [
            "difficulty",
            "gasLimit",
            "gasUsed",
            "number",
            # "size", # FIXME Blocked by SEARCH-140 !! Incorrect `null` value broke self._convert method
            "timestamp",
            # "totalDifficulty", # TODO Why node return null?!
        ]

        result = self._convert(numeric, uncle)
        del(result["blockNumber"])

        return result


class Jsearch():
    def __init__(self, url):
        self.url = url
        self.convert = JsearchToRpcDataConverter()

    def _get_data(self, url, status_code=200):
        response = requests.get(url)
        assert (response.status_code == status_code)
        result = json.loads(response.text)
        return result

    def block_by_number(self, number):
        url = path.join(self.url, 'blocks', str(number))
        data = self._get_data(url)
        result = self.convert.block(data)
        return result

    def block_by_hash(self, block_hash):
        url = path.join(self.url, 'blocks', block_hash)
        data = self._get_data(url)
        result = self.convert.block(data)
        return result

    def block_transactions(self, block_number):
        url = path.join(self.url, 'blocks', str(block_number), 'transactions')
        data = self._get_data(url)
        result = [self.convert.transaction(item) for item in data]
        return result

    def block_uncles(self, block_number):
        url = path.join(self.url, 'blocks', str(block_number), 'uncles')
        data = self._get_data(url)
        result = [self.convert.uncle(item) for item in data]

        return sorted(result, key=lambda x: x['hash'])

    def block_list(self, limit=20, offset=0):
        url = path.join(self.url, 'blocks')
        url += '?limit={0}&offset={1}'.format(limit, offset)

        data = self._get_data(url)
        result = [self.convert.block(item) for item in data]
        return result
