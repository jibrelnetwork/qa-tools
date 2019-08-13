import time
import string
import random
import datetime
from dateutil.relativedelta import relativedelta


class ClassPropertyDescriptor(object):

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


def getter(path, data, default=None):
    """
    Simple getting values from data structure
    example:
        uber = {'type': 5, 'data': [12, ['1', '2', {'asd': 'zxc'}], 14]}
        getter('data.1.2', uber)
    returns
        {'asd': 'zxc'}
    If path not found - returns None
    """
    # print 'data', path, data
    if path is None:
        return data
    try:
        if '.' in path:
            lpath, rpath = path.split('.', 1)
        else:
            lpath = path
            rpath = None

        if isinstance(data, (list, tuple, set)) and lpath.isdigit():
            return getter(rpath, data[int(lpath)], default)
        elif isinstance(data, dict):
            return getter(rpath, data[lpath], default)
        else:
            return getter(rpath, getattr(data, lpath), default)
    except Exception:
        return default


def func_waiter(lambda_fn, timeout=5, wait_time=300, msg="Can't await this function"):
    time_end = time.time() + wait_time
    while time.time() < time_end:
        try:
            data = lambda_fn()
            return data
        except:
            time.sleep(timeout)
    raise TimeoutError(msg)


def generate_value(size=10, chars=string.ascii_uppercase + string.digits, prefix='', suffix=''):  # TODO: add string.punctuation?
    len_pref, len_suff = len(prefix), len(suffix)
    if len_pref + len_suff >= size:
        raise Exception("Can't generate random string. Long suffix or/and  prefix")
    size = size - len_pref - len_suff
    random_string = ''.join([prefix] + [random.choice(chars) for _ in range(size)] + [suffix])
    return random_string


def generate_hex(size=10, with_prefix=True):
    data = generate_value(size, string.hexdigits)
    if with_prefix:
        data = '0x' + data
    return data


def generate_address():
    return generate_hex(40)


def generate_number(min=0, max=10, is_float=False):
    if is_float:
        return random.uniform(min, max)
    else:
        return random.randint(min, max)


def generate_date(change_value=0, change_type='days', format='%Y-%m-%dT%H:%M:%SZ'):
    date = datetime.datetime.utcnow()
    if change_value:
        date += relativedelta(**{change_type: change_value})
    if format:
        return date.strftime(format)
    else:
        return date


if __name__ == "__main__":
    print(generate_value(prefix='qwewqeqwe'))
    print(generate_value(suffix='qwewqeqwe'))
    print(generate_value(prefix='123', suffix='123'))
    # generate_value(prefix='123', suffix='qwewqeqwe1')
    # generate_value(suffix='qwewqeqwe1')
    generate_value(prefix='qwewqeqweq')

