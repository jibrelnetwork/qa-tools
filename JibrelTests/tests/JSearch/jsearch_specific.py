import logging
from web3 import Web3
from JibrelTests.actions.common import ClientApi


log = logging.getLogger(__name__)


class NodeToJsearchDataConverter:
    def __init__(self):
        pass

    @staticmethod
    def _convert(original, hex_to_int=None):
        default_keys = ["difficulty", "gasLimit", "gasUsed", "number", "timestamp",
        # "size", # FIXME Blocked by SEARCH-140 !! Incorrect `null` value broke self._convert method
        # "totalDifficulty", # TODO Why node return null?!
        ]
        hex_to_int = hex_to_int if hex_to_int is not None else default_keys
        converted = dict(original)
        for key in hex_to_int:
            log.warning('key: %s, value: %s' % (key, original[key]))
            converted[key] = int(original[key], 16)
        return converted

    def block(self, original):
        return self._convert(original)

    def uncle(self, original):
        return self._convert(original)

    def transaction(self, original):
        return self._convert(original, ("blockNumber", "transactionIndex"))


class Validator:
    def __init__(self):
        self.convert = NodeToJsearchDataConverter()

    @staticmethod
    def difference(one: dict, two: dict):
        only_in_one = set()
        only_in_two = set()
        diff = set()

        for key in one:
            if key in two:
                if one[key] != two[key]:
                    diff.add(key)
            else:
                only_in_one.add(key)

        for key in two:
            if key not in one:
                only_in_two.add(key)

        return diff, only_in_one, only_in_two

    def validate_data_dict(self, actual, expected, act_only=None, exp_only=None):
        act_only = act_only or set()
        exp_only = exp_only or set()

        diff, act, exp = self.difference(actual, expected)

        if diff != set():
            for item in diff:
                log.error('actual %s: %s' % (item, actual[item]))
                log.error('expected %s: %s' % (item, expected[item]))
        if act != act_only:
            log.error('Actual additional keys (fact) %s' % act)
            log.error('Actual additional keys (expected) %s' % act_only)
        if exp != exp_only:
            log.error('Reference additional keys (fact) %s' % exp)
            log.error('Reference additional keys (expected) %s' % exp_only)

        return all((diff == set(), act == act_only, exp == exp_only))

    def block(self, actual, expected):
        expected_ = self.convert.block(expected)
        act_only = set(('txFees', 'staticReward', 'uncleInclusionReward'))

        common_valid = self.validate_data_dict(actual, expected_, act_only)

        # FIXME add correct validation for block rewards
        #   ('txFees', 'staticReward', 'uncleInclusionReward')
        #   ~ ~ ~
        #   variant #1 use Etherscan API
        #   variant #2 use expected range based on Geth release notes


        # expected_rewards = es.get_block_rewards(expected['number'])
        # summary_reward = int(actual['staticReward'], 16) +\
        #                  int(actual['txFees'], 16)
        reward_valid = True

        return all((common_valid, reward_valid))

    def uncle(self, actual, expected):
        # Uncles inside uncle is absent in API response
        # because it's not interesting for end users

        params = {
            'actual': actual,
            'expected': self.convert.uncle(expected),
            'act_only': set(("reward", "blockNumber")),
            'exp_only': set(["uncles"]) # not needed when use web3py
        }
        return self.validate_data_dict(**params)

    def transaction(self, actual, expected):
        expected_ = self.convert.transaction(expected)
        return self.validate_data_dict(actual, expected_)


class Eth:
    """
    To simplify data comparison, because Web3 use in response
        specific data types (AttributeDict, HexBytes).
    """

    def __init__(self, url):
        self._client = ClientApi(url)
        self._json_header = {"jsonrpc": "2.0", "id": 777}

    def _result(self, body):
        body.update(self._json_header)
        _, response = self._client.post('', body)
        log.debug(response)
        return response['result']

    def getBlock(self, tag, full_transactions=False):
        if type(tag) == str and tag not in ('latest',):
            body = {'method': 'eth_getBlockByHash'}
        else:
            body = {'method': 'eth_getBlockByNumber'}

        if type(tag) == int:
            body['params'] = [hex(tag), full_transactions]
        else:
            body['params'] = [tag, full_transactions]

        return self._result(body)

    def getUncle(self, tag, index):
        if type(tag) == str and tag not in ('latest',):
            body = {'method': 'eth_getUncleByBlockHashAndIndex'}
        else:
            body = {'method': 'eth_getUncleByBlockNumberAndIndex'}

        if type(tag) == int:
            body['params'] = [hex(tag), hex(index)]
        else:
            body['params'] = [tag, hex(index)]

        return self._result(body)


class JsonRpc:
    def __init__(self, url):
        self.eth = Eth(url)


class ReferenceDataProvider():
    def __init__(self, url):
        self.rpc = JsonRpc(url)
        self.web3 = Web3(Web3.HTTPProvider(url))

    def block_transactions(self, tag):
        full_block_data = self.rpc.eth.getBlock(tag, True)
        full_transactions_list = full_block_data["transactions"]
        return full_transactions_list

    def block_uncles(self, tag):
        # Method `eth_getUncleByBlockNumberAndIndex` is missing from web3py
        uncle_count = self.web3.eth.getUncleCount(tag)
        uncle_list = []
        for idx in range(uncle_count):
            uncle_list.append(self.rpc.eth.getUncle(tag, idx))
        print(uncle_list)
        result = sorted(uncle_list, key=lambda x: x['hash'])
        return result

    def eth_getBalance(self, address, block_number):
        payload = {
            "method": "eth_getBalance",
            "params": [address, block_number]
        }
        return self._get_data(payload)

    def eth_getCode(self, address, block_number):
        payload = {
            "method": "eth_getCode",
            "params": [address, block_number]
        }
        return self._get_data(payload)

    def eth_getLogs(self, fromBlock=None, toBlock=None,
                    address=None, topics=None, blockhash=None):
        '''
        blockhash incompatible with fromBlock, toBlock
        '''

        raise NotImplementedError # FIXME

        payload = {
            "method": "eth_getLogs",
            "params": [address, block_number]
        }
        return self._get_data(payload)


class JsearchApiWrapper:
    def __init__(self, url, ver='v1'):
        self.client = ClientApi('/'.join((url, ver)))

    # GET
    def accounts_balances(self, addresses):
        uri = '/accounts/balances'
        query_params = dict(addresses=','.join(addresses))
        return self.client.get(uri, query_params=query_params)

    def accounts(self, address, tag):
        uri = f'/accounts/{address}'
        query_params = dict(tag=tag)
        return self.client.get(uri, query_params=query_params)

    # FIXME limit, offset, order): -> limit=None, offset=None, order=None):
    def accounts_logs(self, address, limit, offset, order):
        uri = f'/accounts/{address}/logs'
        query_params = dict(limit=limit, offset=offset, order=order)
        return self.client.get(uri, query_params=query_params)

    def accounts_transactions(self, address, tag, limit, offset):
        uri = f'/accounts/{address}/transactions'
        pass

    def accounts_internal_transactions(self, address, tag, limit, offset):
        uri = f'/accounts/{address}/internal_transactions'
        pass

    def accounts_pending_transactions(self, address, tag, limit, offset):
        uri = f'/accounts/{address}/pending_transactions'
        pass

    def accounts_mined_blocks(self, address, limit, offset, order):
        uri = f'/accounts/{address}/mined_blocks'
        query_params = dict(limit=limit, offset=offset, order=order)
        return self.client.get(uri, query_params=query_params)

    def accounts_mined_uncles(self, address, limit, offset, order):
        uri = f'/accounts/{address}/mined_uncles'
        query_params = dict(limit=limit, offset=offset, order=order)
        return self.client.get(uri, query_params=query_params)

    def accounts_token_balance(self, address, token_address):
        uri = f'/accounts/{address}/token_balance/{token_address}'
        pass

    def accounts_token_transfers(self, address, limit, offset, order):
        uri = f'/accounts/{address}/token_transfers'
        query_params = dict(limit=limit, offset=offset, order=order)
        return self.client.get(uri, query_params=query_params)

    def blocks(self, limit=None, offset=None):
        uri = '/blocks'
        query_params = dict(limit=limit, offset=offset)
        return self.client.get(uri, query_params=query_params)

    def blocks_tag(self, tag):
        uri = f'/blocks/{tag}'
        return self.client.get(uri)

    def blocks_transactions(self, tag):
        uri = f'/blocks/{tag}/transactions'
        return self.client.get(uri)

    def blocks_uncles(self, tag):
        uri = f'/blocks/{tag}/uncles'
        return self.client.get(uri)

    def transactions(self, txhash):
        uri = f'/transactions/{txhash}'
        return self.client.get(uri)

    def transactions_internal(self, txhash):
        uri = f'/transactions/internal/{txhash}'
        return self.client.get(uri)

    def transactions_pending(self, txhash):
        # FIXME not in Swagger but in code!!
        uri = f'/transactions/pending/{txhash}'
        return self.client.get(uri)

    def receipts(self, txhash):
        uri = f'/receipts/{txhash}'
        return self.client.get(uri)

    def uncles(self, limit, offset, order):
        uri = '/uncles'
        query_params = dict(limit=limit, offset=offset, order=order)
        return self.client.get(uri, query_params=query_params)

    def uncles_tag(self, tag):
        uri = f'/uncles/{tag}'
        return self.client.get(uri)

    # FIXME where it in code:
    # /verified_contracts
    # /verified_contracts/{address}
    # /tokens
    # /tokens/{address}

    def tokens_transfers(self, address, limit, offset, order):
        uri = f'/tokens/{address}/transfers'
        query_params = dict(limit=limit, offset=offset, order=order)
        return self.client.get(uri, query_params=query_params)

    def tokens_holders(self, address, limit, offset, order):
        uri = f'/tokens/{address}/holders'
        query_params = dict(limit=limit, offset=offset, order=order)
        return self.client.get(uri, query_params=query_params)

    def gas_price(self):
        uri = '/gas_price'
        return self.client.get(uri)

    # POST
    def verify_contract(self):
        # FIXME not in Swagger but in code!!
        uri = '/verify_contract'
        return self.client.post(uri)

    def transaction_count(self):
        uri = '/transaction_count'
        return self.client.post(uri)

    def estimate_gas(self):
        uri = '/estimate_gas'
        return self.client.post(uri)

    def call_contract(self):
        uri = '/call_contract'
        return self.client.post(uri)

    def send_raw_transaction(self):
        uri = '/send_raw_transaction'
        return self.client.post(uri)


class Etherscan():

    def __init__(self, api_token='YourApiKeyToken'):
        self.client = ClientApi('https://api.etherscan.io/api')
        self.api_token = api_token

    def get_block_rewards(self, block_number):

        query_params = {
            "module": "block",
            "action": "getblockreward",
            "blockno": block_number,
            "apikey": self.api_token
        }

        status_code, response = self.client.get('', query_params=query_params)
        data = response["result"]

        result = {
            "staticReward": hex(int(data["blockReward"])),
            "uncleInclusionReward": hex(int(data["uncleInclusionReward"])),
            # "unclesReward": [idx["blockreward"] for idx in data["uncles"]]
        }

        return result
