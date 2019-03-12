import pytest
from web3 import Web3
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples_cascade

positive = {
    'address': {
        'mining_pool': '0x52bc44d5378309EE2abF1539BF71dE1b7d7bE3b5', # Etherscan could not found a records
        'contract': '0x8E870D67F660D95d5be530380D0eC0bd388289E1',
    },
    'tag' : {
        'not_set': None,
        'seven M': 7000000,
        'seven M tag': "0x17aa411843cb100e57126e911f51f295f5ddb7e9a3bd25e708990534a828c4b7"
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
        'maximum': 'latest',
        'inside_range': 0.44,
    }
}


@pytest.mark.parametrize("address, tag, limit, offset",
                         **names_and_samples_cascade(positive))
def test_accounts_transactions_positive(address, tag, limit, offset, setup):
    jsearch, reference, _ = setup

    # status_code, response = jsearch.accounts_transactions(address, tag,
    #                                                       limit, offset)
    # assert status_code == StatusCodes.OK
    # assert response['status'] == {"success": True, "errors": []}

    # TODO

    expected = reference.etherscan.getLogs(address, 7200000, 7200200)
    # print(len(response['data']))
    print(len(expected))
    assert None
    # assert response['data'][1] == expected