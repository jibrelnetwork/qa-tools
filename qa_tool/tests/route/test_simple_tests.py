from qa_tool.libs.reporter import reporter


def test_pos_simple_test():
    with reporter.step('Keks login successfull'):
        print('qwe')
        assert 1 == 1

@reporter.label("jira", "CMENABACK-135")
def test_neg_simple_test():
    with reporter.step('Keks login successfull'):
        print('ololo')
        assert 1 == 2


if __name__ == '__main__':
    from qa_tool import run_test
    run_test(__file__.rsplit('/', 1)[0])
