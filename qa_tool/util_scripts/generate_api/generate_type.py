import re
from copy import deepcopy



class JsonFields(object):
    TYPE = "type"
    ITEMS = "items"
    REF = "$ref"
    ONE_OF = "oneOf"
    PROPERTIES = "properties"
    REQUIRED = 'required'
    ADDITIONAL_PROPS = 'additionalProperties'


class JsonTypes(object):
    ARRAY = "array"
    STRING = "string"
    BOOLEAN = "boolean"
    OBJECT = "object"


CLASS_TYPE_TEMPLATE = """
class {def_name}(object):
    @classproperty
    def schema(cls):
        return {type_schema}
"""


def get_def_name_from_ref(ref):
    return ref.split('/')[-1]


def get_array_format_info(array_obj, import_prefix=''):
    if JsonFields.TYPE not in array_obj[JsonFields.ITEMS]:
        array_obj[JsonFields.ITEMS] = field_formatter(deepcopy(array_obj[JsonFields.ITEMS]), import_prefix)
    return array_obj


def get_oneof_format_info(one_of_obj):
    return [field_formatter(i) for i in one_of_obj]


def field_formatter(field_info, import_prefix=''):
    if JsonFields.REF in field_info:
        return get_def_name_from_ref(field_info[JsonFields.REF]) + '.schema'
    if JsonFields.ONE_OF in field_info:
        return {JsonFields.ONE_OF: get_oneof_format_info(field_info[JsonFields.ONE_OF])}
    # if not field_info or JsonFields.TYPE not in field_info:
    #     field_info[JsonFields.TYPE] = JsonTypes.STRING
    type_ = field_info.get(JsonFields.TYPE)
    if type_ == JsonTypes.ARRAY:
        return get_array_format_info(field_info, import_prefix)
    if type_ == JsonTypes.OBJECT:
        if JsonFields.ADDITIONAL_PROPS in field_info:
            field_info[JsonFields.ADDITIONAL_PROPS] = field_formatter(field_info[JsonFields.ADDITIONAL_PROPS])
            return field_info
        for k, v in field_info[JsonFields.PROPERTIES].items():
            field_info[JsonFields.PROPERTIES][k] = field_formatter(v)
    if type_ == JsonTypes.STRING:
        nullable = field_info.pop('nullable', False)
        if nullable:
            field_info[JsonFields.TYPE] = [type_, 'null']
    return field_info


class CombType:
    ANY_OF = 'anyOf'
    ALL_OF = 'allOf'
    ONE_OF = 'oneOf'


def gen_combining_type(field_info, combining_name):
    data = []
    for i in field_info[combining_name]:
        data.append(generate_type_schema(i, format_to_schema=False))
    data = {combining_name: data}
    return data


def generate_type_schema(props, type_prefix=None, format_to_schema=True):
    result = {JsonFields.TYPE: JsonTypes.OBJECT, JsonFields.PROPERTIES: {}}
    if CombType.ALL_OF in props:
        data = gen_combining_type(props, CombType.ALL_OF)
        return format_schema_class(str(data), None)
    def_info = props.get(JsonFields.PROPERTIES, {})
    for field_name, field_info in def_info.items():
        if field_info.get(JsonFields.TYPE) == JsonTypes.OBJECT:
            data = generate_type_schema(field_info, 'types', False)
        elif CombType.ALL_OF in field_info:
            data = gen_combining_type(field_info, CombType.ALL_OF)
        elif CombType.ANY_OF in field_info:
            data = gen_combining_type(field_info, CombType.ANY_OF)
        else:
            data = field_formatter(field_info, 'types')

        result[JsonFields.PROPERTIES][field_name] = data
    if not def_info:
        formatted_field = field_formatter(props)
        if isinstance(formatted_field, str):
            result = [formatted_field]
            if type_prefix:
                result = [type_prefix] + result
            result = '.'.join(result)
        else:
            result = formatted_field
    if not format_to_schema:
        return result
    return format_schema_class(str(result), type_prefix)


def format_schema_class(str_class, type_prefix):
    repl = type_prefix + '.' + r"\1" if type_prefix else r"\1"
    data = re.compile(r"\'([\w]+\.schema)\'").sub(repl, str_class)
    return data


def generate_types(swagger_data):
    generated_definitions = []
    if 'components' in swagger_data:
        all_definitions = swagger_data['components']['schemas']
    else:
        all_definitions = swagger_data['definitions']
    for def_name, props in all_definitions.items():
        schema = generate_type_schema(props)
        generated_definitions.append(CLASS_TYPE_TEMPLATE.format(def_name=def_name, type_schema=schema))
    return "\n".join(generated_definitions)


if __name__ == "__main__":
    # pass
    from qa_tool.util_scripts.generate_api.generate_common import get_swagger_data
    print(generate_types(get_swagger_data('http://127.0.0.1:8000/api/doc/swagger.json')))


