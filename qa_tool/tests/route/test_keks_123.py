from qa_tool.libs.reporter import reporter


@reporter.scenario
class TestKeks123:

    @classmethod
    def setup_class(cls):
        for i in range(2):
            with reporter.step(f'Check setup in one step aggregate'):
                print('kekasdsadasds')

    def setup(self):
        for i in range(2):
            with reporter.step(f'Check setup in one step aggregate'):
                print('asdsadas')

    def teardown(self):
        for i in range(2):
            with reporter.step(f'Check teardown in one step aggregate'):
                print('asdasdasd')

    @classmethod
    def teardown_class(cls):
        for i in range(2):
            with reporter.step(f'Check teardown_class in one step aggregate'):
                print('super test')

    def test_pos_keks123(self):
        with reporter.step('Keks super successfull'):
            print('pos keks')
            assert 1 == 1

    def test_neg_keks123(self):
        with reporter.step('Keks not super successfull'):
            print('neg keks')
            assert 1 == 2


if __name__ == '__main__':
    from qa_tool import run_test
    run_test(__file__)
