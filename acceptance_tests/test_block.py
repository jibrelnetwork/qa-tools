import os
from reuseable import Node, Jsearch
import pytest


jsearch = Jsearch(os.environ['JSEARCH_URL'])
node = Node(os.environ['NODE_URL'])


test_data = {
    'no_uncles_block' : {
        'number' : 4500000,
        'hash' : "0x43340a6d232532c328211d8a8c0fa84af658dbff1f4906ab7a7d4e41f82fe3a3",
    },

    'two_uncles_block' : {
        'number' : 4761173,
        'hash' : "0x3a719fa68bd6a6a777c9041a7200aae35fb639b158591f47e513eda82b340db2",
    },

    # TODO find a block without transactions
    'no_transactions_block' : {
        'number' : None,
        'hash' : None,
    },

    'many_transactions_block' : {
        'number' : 4500000,
        'hash' : "0x43340a6d232532c328211d8a8c0fa84af658dbff1f4906ab7a7d4e41f82fe3a3",
    }

}


def block_by_number(block_number):

    expected = node.block_by_number(block_number)
    actual = jsearch.block_by_number(block_number)

    assert expected == actual


def block_by_hash(block_hash):

    expected = node.block_by_hash(block_hash)
    actual = jsearch.block_by_hash(block_hash)

    assert expected == actual


def block_transactions(block_number):

    expected = node.block_transactions(block_number)
    actual = jsearch.block_transactions(block_number)

    assert expected == actual


def block_uncles(block_number):

    expected = node.block_uncles(block_number)
    actual = jsearch.block_uncles(block_number)

    # It's absent in API response because  it's not intresting for end users
    for item in expected:
        del(item["uncles"]) 
    
    # FIXME: для "reward" добавить проверку на вхождение в допустимый диапазон
    for item in actual:
        del(item["reward"])

    assert expected == actual


def blocks(limit, offset):

    latest_before = jsearch.block_by_number("latest")
    block_list = jsearch.block_list(limit, offset)
    latest_after = jsearch.block_by_number("latest")

    difference = latest_after - latest_before

    # FIXME должен ЛИ список быть уже отсортирован [latest ... earlier]

    for item in sorted(block_list, key=lambda x: int(x["blockNumber"], 16)):

        # номера блоков должны идти подряд
        ... # TODO

        # timestamp'ы должны убывать'
        ... # TODO

        expected = node.block_by_number(int(item["blockNumber"], 16))

        assert item == expected


@pytest.mark.parametrize('case', [
        'no_uncles_block',
        'two_uncles_block',
        'many_transactions_block',
    ])
def test_block_by_number(case):
    block_by_number(test_data[case]['number'])


@pytest.mark.parametrize('case', [
        'no_uncles_block',
        'two_uncles_block',
        'many_transactions_block',
    ])
def test_block_by_hash(case):
    block_by_hash(test_data[case]['hash'])


@pytest.mark.parametrize('case', [
        'many_transactions_block',
    ])
def test_block_transactions(case):
    block_transactions(test_data[case]['number'])


@pytest.mark.parametrize('case', [
        'no_uncles_block',
        'two_uncles_block',
    ])
def test_block_uncles(case):
    block_uncles(test_data[case]['number'])
