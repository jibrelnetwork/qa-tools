import logging
import pytest
from web3 import Web3
from JibrelTests.actions.common import StatusCodes
from JibrelTests.tests.JSearch.checklist_helper import names_and_samples


log = logging.getLogger(__name__)


test_data_negative = {
    'empty list': [
    ],
    'correct non-existent address (I hope)': [
        '0xafaEEEafaEEEafaEEEafaEEEafaEEEafaEEEafaF'
    ],
    'incorrect address': [
        'incorrect data, sad... but true !',
    ],
    'transaction address': [
        '0x19e65033bf783c34219486869dde7de23e1f7b2dd841068f5e5c122f3e448477'
    ],
    'block address': [
        '0xa1bf23abc96becd302f9ba0e4e5dc945dcff35682ba64c7133f4f2051cf6b4f7',  # Block Height: 7249870
    ],
    'uncle address': [
        '0xed4ff30b964abe09a0654c1d55f6eec0062b3d58c305e9139742c3558fa15fdf',  # Uncle Height: 7246993
    ],
}
test_data_positive = {
    'the one correct existing address': [
        '0x0000000000000000000000000000000000000000'
    ],
    'several correct existing addresses': [
        # '0x8d12A197cB00D4747a1fe03395095ce2A5CC6819',   # EtherDelta_2 # FIXME JSEARCH-168
        '0xAfdbcf2eC150Eaf3535FE3a420fdf3418Ca397d4',   # random from es.io
        '0xFc9Fe93f78265c62DBB08EbF8cd77305e36fC2fF'    # random from es.io
    ],
    'correct existing address is repeated several times': [
        '0xC9C422a5269a82A086AA7fAfAea9E60B013a4DBF',
        '0xAfdbcf2eC150Eaf3535FE3a420fdf3418Ca397d4',   # first
        '0x4bc9234A7A268b1B374cC2e259422201caB16Fab',
        '0xAfdbcf2eC150Eaf3535FE3a420fdf3418Ca397d4',   # second
        '0x6D87c95546abd08912468208EEe51319AD9c7F94',
    ],
    'some addresses in the checksum format, some in lower_case': [
        '0x6D87c95546abd08912468208EEe51319AD9c7F94',
        '0x875c2aa1b9772fe760e330c2fb18a1853dcce8ec'
    ],
    'account addresses': [
        '0x51f9C432A4e59aC86282D6ADaB4c2EB8919160EB',
        '0x2140eFD7Ba31169c69dfff6CDC66C542f0211825',
    ],
    'contract addresses': [
        "0xa5Fd1A791C4dfcaacC963D4F73c6Ae5824149eA7",    # JNT
        # '0xE3775d7155987A81a438cD4Ab168d2692b1b4B5D'   # does not exist on block '0x6dffe5'
    ],
    'the mining pool address (updatable non-zero balance at any time)': [
        '0x52bc44d5378309EE2abF1539BF71dE1b7d7bE3b5'    # Nanopool
    ],
    #  For more clear check next addresses should be different from any addresses above
    #  Because Postgres cached requests
    'the maximum number of addresses': [
            # '0xB6B9bAD197225DEda72f452A2660F813B557cCc2', # FIXME JSEARCH-168
            '0x121EFFb8160f7206444f5a57d13c7A4424a237A4',
            '0x53E0003bb8D64D5F4E4e75Be519e119E44288660',
        ]*70,
    'more than the maximum number of addresses': [
            # '0xeD212a4A2E82d5ee0D62F70B5deE2f5Ee0f10c5D', # FIXME JSEARCH-168
            '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B'
        ]*1000,
}


def reference_data_is_up_to_date(jsearch, reference):
    status_code, response = jsearch.blocks_tag("latest")
    latest_jsearch_number = response['data']['number']
    latest_jsearch_hash = response['data']['hash']

    latest_reference = int(reference.rpc.eth.getBlock("latest")['number'], 16)

    if latest_reference < latest_jsearch_number:
        message = ' '.join(
            ('Reference data is out of date!',
             'Jsearch latest block is: `%s`.',
             'ReferenceData latest block is: `%s`.')
        )
        raise ValueError(message % (latest_jsearch_number, latest_reference))

    reference_block = reference.rpc.eth.getBlock(latest_jsearch_number)
    reference_block_hash = reference_block['hash']

    log.info(latest_jsearch_number)
    log.info(latest_jsearch_hash)
    log.info(reference_block_hash)

    if latest_jsearch_hash != reference_block_hash:
        message = ' '.join(
            ('Latest Jsearch block (number: `%s`) in Fork!',
             'Jsearch block hash: `%s`.',
             'ReferenceData block hash: `%s`.')
        )
        params = (latest_jsearch_number, latest_jsearch_hash, reference_block_hash)
        raise ValueError(message % params)

    return hex(latest_jsearch_number)


@pytest.mark.parametrize("address_list", **names_and_samples(test_data_positive))
def test_accounts_balances_positive(address_list, setup):
    jsearch, reference, _ = setup
    latest = reference_data_is_up_to_date(jsearch, reference)
    log.debug('Jsearch latest block is %s' % latest)
    status_code, response = jsearch.accounts_balances(address_list)
    assert status_code == StatusCodes.OK
    assert response['status'] == {"success": True, "errors": []}

    # Minimize requests to ReferenceData Node
    storage = {}
    for address in set(address_list):
        checksum_address = Web3.toChecksumAddress(address)
        storage[address] = hex(reference.web3.eth.getBalance(checksum_address, latest))

    expected = []
    for address in address_list:
        balance = storage[address]
        expected.append(dict(balance=balance, address=address.lower()))

    assert response['data'] == expected


@pytest.mark.parametrize("address_list", **names_and_samples(test_data_negative))
def test_accounts_balances_negative(address_list, setup):
    jsearch, _, _ = setup
    status_code, response = jsearch.accounts_balances(address_list)
    assert status_code == StatusCodes.OK
    assert response == {'status': {"success": True, "errors": []}, 'data': []}
