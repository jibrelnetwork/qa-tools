import re
from qa_tool.utils.common import Methods
from qa_tool.util_scripts.generate_api.generate_type import generate_type_schema, JsonFields, JsonTypes, get_def_name_from_ref

AS_TYPE_IMPORT = 'types'
REQUIRED_SUFFIX_TYPES = ['Required', 'Optional']


CLASS_TEMPLATE = """
class {interface_name}(object):
    def __init__(self, client):
        self.client = client
"""


METHOD_TEMPLATE = """
    @validate_type_wrap({validate_type})
    def {method_name}(self, {method_signature}):
        uri = f"{uri_path}"
        body = {body_payload}
        query_params = {query_params}
        return self.client.{request_method}(uri, body, query_params)
"""


# def _get_body_params(definition_name, definitions, depth=None):
#
#     definition = get_def_name_from_ref(definition_name)
#     assert definition in definitions, f"Definition '{definition}' not exist"
#     definition_info = definitions[definition]
#     definition_type = definition_info.get(JsonFields.TYPE)
#     if not definition_type:
#         raise Exception('Need add this behavior')
#     if definition_type == JsonTypes.OBJECT:
#         result = {i: {} for i in definition_info[JsonFields.PROPERTIES]}
#         for param_name, param_info in definition_info[JsonFields.PROPERTIES].items():
#             result[param_name]['required'] =
#     else:
#         raise Exception('Need add this behavior')


def _get_query_params_and_body(params):
    body = {}
    query = []
    for param in params:
        if JsonFields.REF in param:
            query.append(get_def_name_from_ref(param[JsonFields.REF]))
        elif param.get(JsonFields.TYPE, JsonTypes.OBJECT) != JsonTypes.OBJECT:
            query.append(param['name'])
        elif 'schema' in param:
            schema = param['schema']
            if JsonFields.REF in schema:
                body = get_def_name_from_ref(schema[JsonFields.REF])
            elif schema['type'] == JsonTypes.ARRAY:
                if not isinstance(body, dict):
                    raise Exception("Can't detect body payload for method")
                items = schema['items']
                if JsonFields.REF in items:
                    body = get_def_name_from_ref(items[JsonFields.REF]) + 's'
                elif JsonFields.TYPE in items:
                    body = items[JsonFields.TYPE] + '_array'
                body = body.lower()
                continue
            elif schema['type'] in (JsonTypes.STRING, JsonTypes.BOOLEAN):
                query.append(param['name'])
                continue
    query = [delete_required_type(i) for i in query]
    return query, body


def _get_uri_params(uri_path):
    return re.findall(r'\{([\w]+)\}', uri_path)


def get_name_by_summary(summary_info):  # TODO: remove after Aleksey Selikhov fixes
    summary = summary_info['summary'].split(' ')
    summary = [i.capitalize() for i in summary]
    return ''.join(summary)


def get_method_name(method_info):
    if 'operationId' in method_info:
        data = method_info['operationId']
    else:
        data = get_name_by_summary(method_info)
    return data.replace('.', '')


def get_validate_definition(method_info):
    responses = method_info['responses']
    for service_code, code_info in responses.items():
        if not service_code.startswith('2'):
            continue
        if 'content' in code_info:
            code_info = code_info['content']['application/json']
        return generate_type_schema(code_info.get('schema', code_info), 'types')
    else:
        raise Exception("Can't detect 2XX service code")


def delete_required_type(param):
    for suff in REQUIRED_SUFFIX_TYPES:
        if suff in param:
            return param.replace(suff, '')
    return param


def get_stringify_params(params):
    if params:
        butter = "{%s\n        }"
        template = '\n' + ' ' * 12 + '"%s": %s,'
        code = [template % (k, k) for k in params]
        return butter % ("".join(code))
    else:
        return "{}"


def get_stringify_payload(params, definitions=None):
    definitions = definitions or {}
    if isinstance(params, str):
        definition = definitions[params]
        properties = definition[JsonFields.PROPERTIES]
        params = {k: field_info.get(JsonFields.REQUIRED, False) for k, field_info in properties.items()}
    if isinstance(params, dict):
        payload = get_stringify_params(params)
        signature = [f"{field_name}{'' if is_required else '=None'}" for field_name, is_required in params.items()]
    return signature, payload


def get_result_formatter_code(uri_params, query_params, body_payload, definitions=None):
    body_signature = [body_payload] if isinstance(body_payload, str) else [i for i in body_payload]
    signature = uri_params + query_params
    query_params = get_stringify_params(query_params)
    body_signature, body_payload = get_stringify_payload(body_payload, definitions)
    signature += body_signature
    return ', '.join(signature), query_params, body_payload


def get_method_code(uri_path, request_method, method_info, full_swagger=None):
    method_name = get_method_name(method_info)
    validate_type = get_validate_definition(method_info)
    uri_params = _get_uri_params(uri_path)
    query_params, body_payload = _get_query_params_and_body(method_info.get('parameters', [])[uri_path.count('{'):])
    method_signature, query_params, body_payload = get_result_formatter_code(
        uri_params, query_params, body_payload, full_swagger['definitions']
    )
    return METHOD_TEMPLATE.format(**locals())


def generate_interface(swagger_data, interface_name):
    result = [CLASS_TEMPLATE.format(interface_name=interface_name)]
    all_paths = swagger_data['paths']
    for uri_path, methods in all_paths.items():
        for request_method, method_info in methods.items():
            if request_method.upper() not in Methods.get_all():
                continue
            result.append(get_method_code(uri_path, request_method, method_info, swagger_data))
    return '\n'.join(result)


if __name__ == "__main__":
    from qa_tool.util_scripts.generate_api.generate_common import get_swagger_data
    print(generate_interface(get_swagger_data('test'), 'lol'))
    print(generate_type_schema({'type': 'object', 'properties': {'status': {'$ref': '#/definitions/Status'}, 'data': {'$ref': '#/definitions/Uncle'}}}))
    # print(generate_interface('qwe'))
