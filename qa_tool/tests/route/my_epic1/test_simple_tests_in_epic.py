from qa_tool.libs.reporter import reporter


def test_pos_simple_test_in_epic():
    with reporter.step('Keks login successfull'):
        print('qwe')
        assert 1 == 1


def test_neg_simple_test_in_epic():
    with reporter.step('Keks login successfull'):
        print('ololo')
        assert 1 == 2


if __name__ == '__main__':
    from qa_tool import run_test
    run_test(__file__.rsplit('/', 1)[0])
