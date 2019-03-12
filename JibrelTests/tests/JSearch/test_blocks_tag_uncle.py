import pytest
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples


test_data_positive = {
    'block by number: no uncles': 4500000,
    'block by number: two uncles': 4761173,

    'block by hash: no uncles': "0x43340a6d232532c328211d8a8c0fa84af658dbff1f4906ab7a7d4e41f82fe3a3",
    'block by hash: two uncles': "0x3a719fa68bd6a6a777c9041a7200aae35fb639b158591f47e513eda82b340db2",
}


@pytest.mark.parametrize("case", **names_and_samples(test_data_positive))
def test_block_uncles(case, setup):
    """
    The API response contains a "reward" field
    that cannot be received from the fast-synced node.
    """
    jsearch, reference, validate = setup
    expected = reference.block_uncles(case)
    status_code, response = jsearch.blocks_uncles(case)

    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}
    assert len(response['data']) == len(expected)

    # FIXME: для "reward" добавить проверку на вхождение в допустимый диапазон
    for idx, actual in enumerate(response['data']):
        assert validate.uncle(actual, expected[idx])

    # TODO: добавить проверку на корректность blockNumber, т.к. наш сервис его возвращает.
