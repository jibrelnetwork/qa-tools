import jsonschema
from functools import wraps

from .common import StatusCodes
from .utils import classproperty
from qa_tool.libs.reporter import reporter


class Error(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'field': {'type': 'string'}, 'code': {'type': 'string'}, 'message': {'type': 'string'}}}


class Errors(object):
    @classproperty
    def schema(cls):
        return {'type': 'array', 'items': Error.schema, 'example': []}


class Status(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'success': {'type': 'boolean'}, 'errors': Errors.schema}}


DEFAULT_ERROR = {
    StatusCodes.BAD_REQUEST: Status
}


def validate_type_wrap(combined_type_or_map):
    def fn_wrapper(fn):
        @wraps(fn)
        def wrap(*args, **kwargs):
            code, data = fn(*args, **kwargs)
            schema = DEFAULT_ERROR.get(code, combined_type_or_map)
            try:
                jsonschema.validate(instance=data, schema=schema)
            except Exception as e:
                reporter.attach('EXCEPTION!!!', str(e))
                raise AssertionError('Validation error! Body not same with schema for %s' % fn.__name__)
            return code, data
        return wrap
    return fn_wrapper


if __name__ == "__main__":
    internal_data = {
        "type": "object",
        "properties": {
            'qwe': {"type": "integer"}
        }
    }

    test_schema = {
        "type": "object",
        "properties": {
            'qwe1': {"type": "string"},
            'qwe2': {"type": "string"},
            'lst1': {"type": "array", "items": {"type": "object"}},
            'map1': internal_data
        },
    }


    @validate_type_wrap(test_schema)
    def test_call():
        resp = {
            'qwe1': 'wewqewqe',
            'qwe2': 'str2',
            'lst1': [123, 1],
            'map1': {'qwe': 123}
        }

        return 200, resp
