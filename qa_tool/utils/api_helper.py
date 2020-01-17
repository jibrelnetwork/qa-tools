import jsonschema
from functools import wraps

from .common import StatusCodes
from .utils import classproperty
from qa_tool.libs.reporter import reporter
from qa_tool.settings import DISABLE_SCHEMA_VALIDATOR


class Error(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'field': {'type': 'string'}, 'code': {'type': 'string'}, 'message': {'type': 'string'}, 'target': {'type': 'string'}}}


class AdditionalError(object):
    @classproperty
    def schema(cls):
        return {'type': 'array', 'properties': {'code': {'type': 'string'}, 'message': {'type': 'string'}}}


class JtickerError(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'success': {'description': 'indicate whole response success', 'type': 'boolean', 'example': True}, 'errors': {'type': 'array', 'description': 'error list', 'items': {'type': 'object', 'description': 'errors by field name (for input errors)', 'properties': {'field': {'type': 'string', 'description': 'error field name'}, 'code': {'type': 'string', 'description': 'machine-readable error code'}, 'message': {'type': 'string', 'description': 'error message'}, 'details': {'type': 'object', 'description': 'details properties of error', 'properties': {'asset': {'type': 'string', 'description': 'asset from error'}, 'exchange': {'type': 'string', 'description': 'exchange from error'}}}}}}}}


class Errors(object):
    @classproperty
    def schema(cls):
        data = [
            {'type': 'array', 'items': Error.schema},
            {'type': 'object', 'additionalProperties': AdditionalError.schema},
            JtickerError.schema
        ]
        return {'oneOf': data}


class Status(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'success': {'type': 'boolean'}, 'errors': Errors.schema}}


DEFAULT_ERROR = {
    StatusCodes.BAD_REQUEST: Status.schema,
    StatusCodes.FORBIDDEN: Status.schema,
    StatusCodes.CONFLICT: Status.schema,
    StatusCodes.TOO_MANY_REQUESTS: Status.schema,
}


def validate_type_wrap(combined_type_or_map):
    def fn_wrapper(fn):
        @wraps(fn)
        def wrap(*args, **kwargs):
            try:
                service_name = args[0].__class__.__name__
            except:
                service_name = 'UNDEFINED SERVICE NAME'
            if DISABLE_SCHEMA_VALIDATOR:
                return fn(*args, **kwargs)
            with reporter.step("Step: request %s to %s service:" % (fn.__name__, service_name)):
                code, data = fn(*args, **kwargs)
                schema = DEFAULT_ERROR.get(code, combined_type_or_map)
                try:
                    jsonschema.validate(instance=data, schema=schema)
                except Exception as e:
                    reporter.attach('Schema validation exception!', str(e))
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
