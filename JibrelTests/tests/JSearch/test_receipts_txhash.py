import pytest
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples


positive = {
    'big_gas_price': '0x1f73b43dc9c48cc131a931fac7095de9e5eba0c5184ec0c5c5f1f32efa2a6bab',
    'no logs': '0x0ed00f09f3c8613fb7a6de4fa76ae68053ec5f022180289e8d5613d126bfb5a0',
    'one log record': '0x527db65edaf3fa7c7938f4943645b160e7e024c6e7c07c03b626c8330ae8ca8f',
    'out of gas': '0xfe578137dc2e2aea437980bc67ebc21d87a3cc64a7419f66ff788560a0d86e13',
    'reverted': '0x9b4d3f3eaa6bd7b89fbbf37207b169f04281c3b6a76d12515b93e357d94e54d9',
    # TODO:
    # 'send ether': ,
    # 'send token': ,
}


@pytest.mark.parametrize("txhash", **names_and_samples(positive))
def test_receipts_positive(txhash, setup):
    jsearch, reference, validate = setup
    status_code, response = jsearch.receipts(txhash)
    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}

    expected = reference.rpc.eth.getTransactionReceipt(txhash)

    assert validate.receipt(response['data'], expected)