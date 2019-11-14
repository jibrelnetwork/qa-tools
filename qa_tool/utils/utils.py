import time
import pytz
import string
import random
import datetime
from functools import wraps
from itertools import islice

from dateutil.parser import parse
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
    error = "Don't catch any exception"
    while time.time() < time_end:
        try:
            data = lambda_fn()
            return data
        except Exception as e:
            error = str(e)
            time.sleep(timeout)
    raise TimeoutError(msg+f"\n{error}")


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


def window(seq, n=2):
    # https://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator
    # "Returns a sliding window (of width n) over data from the iterable"
    # "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def random_pop(list_data, population):
    if population > len(list_data):
        raise Exception('Not enough data for all operations')
    return [list_data.pop(generate_number(0, len(list_data) - 1)) for _ in range(population)]


def to_list(data):
    return data if isinstance(data, (list, tuple)) else [data]


def timing_fn(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kw, time.time()-ts))
        return result
    return wrap


class TimeUtil:

    @classproperty
    def _now(self):
        return datetime.datetime.now()

    @classmethod
    def to_date(cls, date):
        if isinstance(date, datetime.date):
            if date.tzinfo:
                date = date.astimezone(pytz.timezone('UTC'))
            else:
                date = pytz.timezone('UTC').localize(date)
            return date
        if isinstance(date, (float, int)):
            return pytz.timezone('UTC').localize(datetime.datetime.utcfromtimestamp(date))
        return cls.to_date(parse(date))

    @classmethod
    def check_date_in_delta(cls, actual_date, expected_date, delta_seconds=2):
        expected_date = cls.to_date(expected_date)
        delta = relativedelta(seconds=delta_seconds)
        return cls.check_date_in_range(actual_date, expected_date - delta, expected_date + delta)

    @classmethod
    def check_date_in_range(cls, actual_date, time_start, time_end=None):
        time_start = cls.to_date(time_start)
        actual_date = cls.to_date(actual_date)
        time_end = cls.to_date(time_end or cls._now)
        assert time_start < actual_date < time_end, f"{time_start} < {actual_date} < {time_end}"

    @classmethod
    def generate_date_in_range(cls, start_date, end_date=None, step='minutes'):
        start_date = cls.to_date(start_date)
        end_date = cls.to_date(end_date or cls._now)
        step_seconds = (cls._now - (cls._now - relativedelta(**{step: 1}))).total_seconds()
        available_range = (end_date - start_date).total_seconds()
        start_diff = 1 if step == 'minutes' else 0.1
        end_diff = available_range/step_seconds
        assert end_diff > start_diff, "Too small daterange for generate date in this range"
        diff_range = generate_number(start_diff, end_diff, is_float=True)
        return start_date + relativedelta(**{step: diff_range})


if __name__ == "__main__":
    keks1 = TimeUtil.to_date(time.time())
    keks3 = TimeUtil.to_date(datetime.datetime.now())
    # print(keks1)
    # print(keks3)
    # print(TimeUtil._format_to_date(str(datetime.datetime.now())))
    # print(TimeUtil._format_to_date(datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))))
    # print(pytz.timezone('America/Los_Angeles').localize(datetime.datetime.now()))
    # print(TimeUtil._format_to_date(pytz.timezone('America/Los_Angeles').localize(datetime.datetime.now())))
    # print(TimeUtil._format_to_date(str(pytz.timezone('America/Los_Angeles').localize(datetime.datetime.now()))))

    data = TimeUtil.check_date_in_delta(datetime.datetime.now(), datetime.datetime.now())
    TimeUtil.check_date_in_delta(str(datetime.datetime.now()), datetime.datetime.now())
    TimeUtil.check_date_in_delta(time.time(), datetime.datetime.now().astimezone(pytz.timezone('UTC')))
    try:
        TimeUtil.check_date_in_delta(str(pytz.timezone('America/Los_Angeles').localize(datetime.datetime.now())), datetime.datetime.now())
    except:
        print('all is ok')

    TimeUtil.check_date_in_range(time.time()+2.0, datetime.datetime.now().astimezone(pytz.timezone('UTC')))
    TimeUtil.check_date_in_range(time.time()+2.0, datetime.datetime.now())  # TODO: need think about it




    print(generate_value(prefix='qwewqeqwe'))
    print(generate_value(suffix='qwewqeqwe'))
    print(generate_value(prefix='123', suffix='123'))
    # generate_value(prefix='123', suffix='qwewqeqwe1')
    # generate_value(suffix='qwewqeqwe1')
    generate_value(prefix='qwewqeqweq')

