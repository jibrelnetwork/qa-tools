from JibrelTests.actions.common import StatusCodes

number = 7082467
hash_ = "0x71d4bb4662b3449702c64e9ec46b687d2fd3ab4dcd3e2d86e954ad05ce2b6ca0"


def test_received_canonical_block_for_given_number(setup):
    jsearch, reference, validate = setup
    expected = reference.rpc.eth.getBlock(number)

    status_code, response = jsearch.blocks_tag(number)
    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}
    assert validate.block(response['data'], expected)


def test_received_canonical_block_for_given_hash(setup):
    jsearch, reference, validate = setup
    expected = reference.rpc.eth.getBlock(number)

    status_code, response = jsearch.blocks_tag(hash_)
    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}
    assert validate.block(response['data'], expected)


def test_received_not_found_for_given_reorg_hash(setup):
    jsearch, _, _ = setup
    reorg_hash = "0x35775dea08e8bb722474013e49a41d898769b3fe88119b6a9db396c9daf30f06"
    status_code, response = jsearch.blocks_tag(reorg_hash)
    assert status_code == StatusCodes.NOT_FOUND
    assert response is ''
