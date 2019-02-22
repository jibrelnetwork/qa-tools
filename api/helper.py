from functools import wraps
from JibrelTests.actions.common import ServiceCodes


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
        'lst1': {"type": "array", "items": {"type": "integer"}},
        'map1': internal_data
    },
}


class Status:
    pass


DEFAULT_ERROR = {
    ServiceCodes.BAD_REQUEST: Status

}

import jsonschema

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


@validate_type_wrap(test_schema)
def test_call():
    resp = {
        'qwe1': 'wewqewqe',
        'qwe2': 'str2',
        'lst1': [123, 1],
        'map1': {'qwe': 123}
    }

    return 200, resp
