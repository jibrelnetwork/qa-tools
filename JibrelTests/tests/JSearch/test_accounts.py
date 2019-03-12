"""
Проверить смену значений по каждому атрибуту:
    "blockNumber",
    "blockHash",
    "nonce",
    "balance"

Проверить как аккаунты, так и контракты
    "code": "",
    "codeHash": "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
    "address": "0x49df2c97eea73fa42acb829ce5e0b43930bacfb7",

Влияние параметра  tag

"""
import logging
import pytest
from web3 import Web3
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples_cascade


log = logging.getLogger(__name__)


negative = {
    'addres_not_in_blockchain_yet': [
        '0x8E870D67F660D95d5be530380D0eC0bd388289E1',
        4
    ],
    'block_number_greater_than_latest': [
        '0x8E870D67F660D95d5be530380D0eC0bd388289E1',
        8000000
    ],
    'incorrect_block_number': [
        '0x8E870D67F660D95d5be530380D0eC0bd388289E1',
        -1
    ],
    'incorrect_block_hash': [
        '0x8E870D67F660D95d5be530380D0eC0bd388289E1',
        '0xfave'
    ],
    'correct non-existent address (I hope)': [
        '0xafaEEEafaEEEafaEEEafaEEEafaEEEafaEEEafaF',
        None
    ],
    'incorrect address': [
        '0xr2930R35844R230R00E51431rRRr96Rr543r0347',
        None
    ],
}

positive = {
    'address': {
        'account': '0xb2930B35844a230f00E51431aCAe96Fe543a0347',
        'contract': '0x8E870D67F660D95d5be530380D0eC0bd388289E1',
    },
    'tag': {
        'latest',
        '7212000',
        '0x88a6bc42f4f65a0daab3a810444c2202d301db04d05203a86342b35333ac1413',
    }
}


@pytest.mark.parametrize("address, tag",
                         **names_and_samples_cascade(positive))
def test_accounts_balances_positive(address, tag, setup):
    # latest = reference_data_is_up_to_date()
    jsearch, reference, _ = setup

    status_code, response = jsearch.accounts(address, tag)
    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}

    # TODO: add checks
    # expected_code = reference.web3.eth.getCode(address, tag)
    # expected_code_hash = Web3.sha3(text=expected_code).hex()
    # expected = {
    #     "blockNumber": ...,
    #     "blockHash": ...,
    #     "address": address,
    #     "nonce": reference.web3.eth.getTransactionCount(address, tag),
    #     "code": expected_code,
    #     "codeHash": expected_code_hash,
    #     "balance": reference.web3.eth.getBalance(address, tag),
    # }

    # assert response['data'] == expected


@pytest.mark.parametrize("address, tag",
                         **names_and_samples_cascade(negative))
def test_accounts_balances_negative(address, tag, setup):
    pass