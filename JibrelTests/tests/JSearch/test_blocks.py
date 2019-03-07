import pytest
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples_cascade


positive = {
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
    },
}


def expected_blocks_numbers(latest, limit, offset):
    limit = limit if limit is not None else 20
    offset = offset if offset is not None else 0
    first_number = latest - offset
    last_number = first_number - limit
    expected_numbers = list(range(first_number, last_number, -1))
    return expected_numbers


@pytest.mark.parametrize("limit, offset", **names_and_samples_cascade(positive))
def test_blocks(setup, limit, offset):
    """
    {'totalDifficulty': None} != {'totalDifficulty': '0x1e5a7be9d0630a97622'}
    {'uncles': None} != {'uncles': []}
    {'size': None} != {'size': '0x5e8c'}
    {'transactions': None} != {'transactions': ['0xd66ed91687791d57c953e25e2c6d7c424957c4e62dec68da22ec45170ffc6685', '0x262d97359ed41f92eff9b707046...ac2cf682e3b1210b81a4f34323900f6aa8edffeb7', '0x495e29df3ffb57c1079272a5953fd3bb10bb63858f692f3efb44af152829b837', ...]}

    Left contains more items:
    {
    'staticReward': '0x29a2241af62c0000',
    'txFees': '0xca157dd42950e2',
    'uncleInclusionReward': '0x0'
    }
    """
    jsearch, reference, validate = setup

    _, response = jsearch.blocks_tag("latest")
    latest_before = response['data']["number"]

    if offset == 'latest':
        offset = latest_before
    elif isinstance(offset, float):
        offset = int(latest_before * offset)

    status_code, response = jsearch.blocks(limit, offset)
    block_list = response['data']

    _, response = jsearch.blocks_tag("latest")
    latest_after = response['data']["number"]

    # TODO if this condition will brakes it will be need to processed
    assert latest_before == latest_after

    latest = latest_before

    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}

    reference_numbers = expected_blocks_numbers(latest, limit, offset)
    actual_block_numbers = [block["number"] for block in block_list]
    assert actual_block_numbers == reference_numbers

    for idx, actual in enumerate(block_list):
        tag = reference_numbers[idx]
        expected = reference.rpc.eth.getBlock(tag)
        assert validate.block(actual, expected)
