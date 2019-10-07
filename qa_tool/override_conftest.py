import py
from _pytest import nose
from qa_tool.libs.reporter import reporter
from _pytest.python import Class, _get_non_fixture_func


def setup_class_fixture(self):
    setup_class = _get_non_fixture_func(self.obj, 'setup_class')
    if setup_class is not None:
        setup_class = getattr(setup_class, 'im_func', setup_class)
        setup_class = getattr(setup_class, '__func__', setup_class)
        with reporter.step('Setup class'):
            setup_class(self.obj)

    fin_class = getattr(self.obj, 'teardown_class', None)
    if fin_class is not None:
        fin_class = getattr(fin_class, 'im_func', fin_class)
        fin_class = getattr(fin_class, '__func__', fin_class)

        def fin_fn():
            with reporter.step('Teardown class'):
                fin_class(self.obj)

        self.addfinalizer(fin_fn)


def call_optional_override(obj, name):
    method = getattr(obj, name, None)
    isfixture = hasattr(method, "_pytestfixturefunction")
    if method is not None and not isfixture and py.builtin.callable(method):
        # If there's any problems allow the exception to raise rather than
        # silently ignoring them
        with reporter.step('%s test' % name):
            method()
        return True


Class.setup = setup_class_fixture
nose.call_optional = call_optional_override
