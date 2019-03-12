import pytest
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples


test_data_positive = {
    'block by number: no uncles': 4500000,
    'block by number: two uncles': 4761173,
    'block by number: no transactions': 122070,
    'block by number: one transactions': 122069,
    'block by number: many transactions': 4500000,

    'block by hash: no uncles': "0x43340a6d232532c328211d8a8c0fa84af658dbff1f4906ab7a7d4e41f82fe3a3",
    'block by hash: two uncles': "0x3a719fa68bd6a6a777c9041a7200aae35fb639b158591f47e513eda82b340db2",
    'block by hash: no transactions': "0x664007ceffd3c9f78f05bb5e525e76879171e4117edfd19174bb2027e5f95ef4",
    'block by hash: one transactions': "0xff5c610d15ae696d329e1076b873df58c20a2710fe75e9282b6c852b8546bf04",
    'block by hash: many transactions': "0x43340a6d232532c328211d8a8c0fa84af658dbff1f4906ab7a7d4e41f82fe3a3",
}


@pytest.mark.parametrize("case", **names_and_samples(test_data_positive))
def test_block(setup, case):
    jsearch, reference, validate = setup
    expected = reference.rpc.eth.getBlock(case)
    status_code, response = jsearch.blocks_tag(case)

    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}
    assert validate.block(response['data'], expected)
