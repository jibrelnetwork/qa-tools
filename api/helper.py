import jsonschema
from functools import wraps
from JibrelTests.utils.utils import classproperty
from JibrelTests.actions.common import StatusCodes


class Error(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'field': {'type': 'string', 'example': 'NON_FIELD_ERROR'}, 'code': {'type': 'string', 'example': 'ERR_CODE'}, 'message': {'type': 'string', 'example': 'some err text'}}}


class Errors(object):
    @classproperty
    def schema(cls):
        return {'type': 'array', 'items': Error.schema, 'example': []}


class Status(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'success': {'type': 'boolean'}, 'errors': Errors.schema}}


class Call(object):
    @classproperty
    def schema(cls):
        return {'type': 'object', 'properties': {'from': {'type': 'string', 'required': False, 'description': 'The address the transaction is sent from.', 'example': '0x8aff0a12f3e8d55cc718d36f84e002c335df2f4a'}, 'to': {'type': 'string', 'required': False, 'description': 'The address the transaction is directed to.', 'example': '0x5c7687810ce3eae6cda44d0e6c896245cd4f97c6'}, 'gas': {'type': 'string', 'format': 'dec', 'required': False, 'description': 'Integer of the gas provided for the transaction execution.', 'example': '0'}, 'gasPrice': {'type': 'string', 'format': 'dec', 'required': False, 'description': 'Integer of the gas provided for the transaction execution.', 'example': '1'}, 'value': {'type': 'string', 'format': 'dec', 'required': False, 'description': 'Integer of the value sent with this transaction.', 'example': '0'}, 'data': {'type': 'string', 'description': 'Hash of the method signature and encoded parametelrs.', 'example': '0x6740d36c0000000000000000000000000000000000000000000000000000000000000005'}}}


DEFAULT_ERROR = {
    StatusCodes.BAD_REQUEST: Status
}


def validate_type_wrap(combined_type_or_map):
    def fn_wrapper(fn):
        @wraps(fn)
        def wrap(*args, **kwargs):
            code, data = fn(*args, **kwargs)
            schema = DEFAULT_ERROR.get(code, combined_type_or_map)
            jsonschema.validate(instance=data, schema=schema)
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
