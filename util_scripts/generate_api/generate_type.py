import re
from copy import deepcopy


class JsonFields(object):
    TYPE = "type"
    ITEMS = "items"
    REF = "$ref"
    PROPERTIES = "properties"


class JsonTypes(object):
    ARRAY = "array"
    STRING = "string"
    OBJECT = "object"


CLASS_TYPE_TEMPLATE = """
class {def_name}(object):
    @classproperty
    def schema(cls):
        return {type_schema}
"""


def get_def_name_from_ref(ref):
    return ref.split('/')[-1]


def get_array_format_info(array_obj):
    if JsonFields.TYPE not in array_obj[JsonFields.ITEMS]:
        array_obj[JsonFields.ITEMS] = field_formatter(deepcopy(array_obj[JsonFields.ITEMS]))
    return array_obj


def field_formatter(field_info):
    if JsonFields.REF in field_info:
        return get_def_name_from_ref(field_info[JsonFields.REF]) + '.schema'
    if not field_info:  # TODO: REMOVE THIS AFTER fill Contract.abi.items field
        field_info[JsonFields.TYPE] = 'string'
    if field_info[JsonFields.TYPE] == JsonTypes.ARRAY:
        return get_array_format_info(field_info)
    return field_info


def generate_type_schema(props, type_prefix=None):
    result = {JsonFields.TYPE: JsonTypes.OBJECT, JsonFields.PROPERTIES: {}}
    def_info = props.get(JsonFields.PROPERTIES, {})
    for field_name, field_info in def_info.items():
        result[JsonFields.PROPERTIES][field_name] = field_formatter(field_info)
    if not def_info:
        result = field_formatter(props)
    return format_schema_class(str(result), type_prefix)


def format_schema_class(str_class, type_prefix):
    repl = type_prefix + '.' + r"\1" if type_prefix else r"\1"
    data = re.compile(r"\'([\w]+\.schema)\'").sub(repl, str_class)
    return data


def generate_types(swagger_data):
    generated_definitions = []
    all_definitions = swagger_data['definitions']
    for def_name, props in all_definitions.items():
        schema = generate_type_schema(props)
        generated_definitions.append(CLASS_TYPE_TEMPLATE.format(def_name=def_name, type_schema=schema))
    return "\n".join(generated_definitions)


if __name__ == "__main__":
    # pass
    from util_scripts.generate_api.generate_common import get_swagger_data
    print(generate_types(get_swagger_data('test')))
