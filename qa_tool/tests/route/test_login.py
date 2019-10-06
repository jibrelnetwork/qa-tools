import allure

from qa_tool.libs.reporter import reporter


class TestLogin:

    @classmethod
    def setup_class(cls):
        for i in range(2):
            with reporter.step(f'Check setupclass in one step aggregate'):
                print('asdsadasd')

    def setup(self):
        for i in range(2):
            with reporter.step(f'Check setup in one step aggregate'):
                print('asdsadsad')

    def teardown(self):
        for i in range(2):
            with reporter.step(f'Check teardown in one step aggregate'):
                print('sadasdsad')

    def teardown_class(self):
        for i in range(2):
            with reporter.step(f'Check teardown_class in one step aggregate'):
                print('asdsadsad')

    def test_pos_login(self):
        with reporter.step('Keks login successfull'):
            print('pos login')
            assert 1 == 1

    @allure.label("jira", "CMENABACK-100")
    def test_pos_login123(self):
        with reporter.step('Keks login successfull'):
            print('pos login')
            assert 1 == 1

    @reporter.label("jira", "CMENABACK-118")
    def test_neg_login(self):
        with reporter.step('Keks login successfull'):
            print('neg login')
            assert 1 == 2

    def test_neg_login_exception(self):
        with reporter.step('Keks login successfull exception'):
            print('pos login')
            reporter.simple_exception()

    def test_neg_login_assertion(self):
        with reporter.step('Keks login successfull assertion'):
            print('pos login')
            reporter.simple_exception(False)


if __name__ == '__main__':
    from qa_tool import run_test
    run_test(__file__.rsplit('/', 1)[0])
