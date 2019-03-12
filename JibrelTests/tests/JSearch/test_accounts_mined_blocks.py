from functools import partial
import pytest
from web3 import Web3
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples_cascade, names_and_samples
from JibrelTests.tests.JSearch.block_selection import find_overlay_in_etherscan

ETHERSCAN_PAGE_SIZE = 100

positive = {
    'address': {
        'miner': '0xb2930B35844a230f00E51431aCAe96Fe543a0347',
        'mining_pool': '0x52bc44d5378309EE2abF1539BF71dE1b7d7bE3b5', # Etherscan could not found a records
    },
    'limit': {
        'not_set': None,
        'minimum': 1,
        'maximum': 20,
        'inside_range': 9,
    },
    'offset': {
        'not_set': None,
        'minimum': 0,
        'inside_range': 30,
    },
    'order': {
        'not_set': None,
        'asc': 'asc',
        'desc': 'desc'
    },
}

no_data = {
    'big_offset': [
        '0xb2930B35844a230f00E51431aCAe96Fe543a0347',  # address
        None,                                          # limit
        1000000,                                       # offset
        None                                           # order
    ],
    'contract_account': [
        '0x8E870D67F660D95d5be530380D0eC0bd388289E1',  # address
        None,                                          # limit
        None,                                          # offset
        None                                           # order
    ],
    'invalid_address': [
        "I'm not a valid address. Sorry! ",            # address
        None,                                          # limit
        None,                                          # offset
        None                                           # order
    ],
}

bad_value = {
    'invalid_limit': [
        '0xb2930B35844a230f00E51431aCAe96Fe543a0347',  # address
        -1,                                            # limit
        None,                                          # offset
        None,                                          # order
        [                                              # errors
            {
                "field": "limit",
                "error_code": "INVALID_LIMIT_VALUE",
                "error_message": "Limit value should be valid integer, got \"-1\""
            }
        ]
    ],
    'invalid_offset': [
        '0xb2930B35844a230f00E51431aCAe96Fe543a0347',  # address
        None,                                          # limit
        -2,                                            # offset
        None,                                          # order
        [                                              # errors
            {
                "field": "offset",
                "error_code": "INVALID_OFFSET_VALUE",
                "error_message": "Offset value should be valid integer, got \"-2\""
            }
        ]
    ],
    'invalid_order': [
        '0xb2930B35844a230f00E51431aCAe96Fe543a0347',  # address
        None,                                          # limit
        None,                                          # offset
        'bad',                                         # order
        [                                              # errors
            {
                "field": "order",
                "error_code": "INVALID_ORDER_VALUE",
                "error_message": "Order value should be one of \"asc\", \"desc\", got \"bad\""
            }
        ]
    ],
}

@pytest.mark.parametrize("address, limit, offset, order",
                         **names_and_samples_cascade(positive))
def test_accounts_mined_blocks_positive(address, limit, offset, order, setup):
    jsearch, reference, validate = setup

    status_code, response = jsearch.accounts_mined_blocks(address, limit,
                                                          offset, order)
    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}


    for item in response['data']:
        expected = reference.rpc.eth.getBlock(item['number'])
        assert address == Web3.toChecksumAddress(expected['miner'])
    #     FIXME uncomment when block will be with correct values
    #     assert validate.block(item, expected)

    actual_numbers = [item['number'] for item in response['data']]
    get_numbers = partial(reference.etherscan.get_mined_blocks_numbers,
                          address=address, offset=ETHERSCAN_PAGE_SIZE)

    result, numbers = find_overlay_in_etherscan(actual_numbers, get_numbers,
                                                ETHERSCAN_PAGE_SIZE)
    assert result

    start = numbers.index(min(actual_numbers))
    stop = numbers.index(max(actual_numbers)) + 1
    assert actual_numbers == sorted(numbers[start:stop], reverse=True)


@pytest.mark.parametrize("address, limit, offset, order",
                         **names_and_samples(no_data))
def test_accounts_mined_blocks_no_data(address, limit, offset, order, setup):
    jsearch, reference, validate = setup

    status_code, response = jsearch.accounts_mined_uncles(address, limit,
                                                          offset, order)
    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}
    assert response['data'] == []


@pytest.mark.parametrize("address, limit, offset, order, errors",
                         **names_and_samples(bad_value))
def test_accounts_mined_blocks_bad_value(address, limit, offset, order, errors, setup):
    jsearch, reference, validate = setup

    status_code, response = jsearch.accounts_mined_uncles(address, limit,
                                                          offset, order)
    assert status_code == StatusCodes.BAD_REQUEST
    assert response['status']['success'] == False
    assert response['status']["errors"] == errors
    assert response['data'] == None
