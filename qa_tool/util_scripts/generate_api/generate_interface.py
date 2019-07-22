import re
from qa_tool.utils.utils import getter
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


def get_body_params_from_definitions(param, definitions):
    definition = definitions.get(param)
    if not definition:
        return {param: False}
    properties = definition[JsonFields.PROPERTIES]
    return {k: field_info.get(JsonFields.REQUIRED, False) for k, field_info in properties.items()}


def get_query_params_from_definitions(param, definitions):
    definition = definitions.get(param)
    if not definition:
        return param, False
    return definition['name'], definition.get(JsonFields.REQUIRED, False)


def get_signature_args(params):
    return [f"{field_name}{'' if is_required else '=None'}" for field_name, is_required in params.items()]


def get_stringify_params(params, definitions):
    if params:
        butter = "{%s\n        }"
        template = '\n' + ' ' * 12 + '"%s": %s,'
        params = dict(get_query_params_from_definitions(i, definitions) for i in params)
        code = [template % (k, k) for k in params]
        return get_signature_args(params), butter % ("".join(code))
    else:
        return [], "{}"


def get_stringify_payload(params, definitions=None):
    definitions = definitions or {}
    if isinstance(params, str):
        params = get_body_params_from_definitions(params, definitions)
    if isinstance(params, dict):
        _, payload = get_stringify_params(params, definitions)
        signature = get_signature_args(params)
    return signature, payload


def get_result_formatter_code(uri_params, query_params, body_payload, swagger_data=None):
    parameters = getter('components.schemas', swagger_data, {})
    definitions = swagger_data.get('definitions') or getter('components.parameters', swagger_data, {})
    parameters.update(definitions)
    query_signature, query_params = get_stringify_params(query_params, definitions)
    body_signature, body_payload = get_stringify_payload(body_payload, parameters)
    signature = uri_params + query_signature + body_signature
    return ', '.join(signature), query_params, body_payload


def get_method_code(uri_path, request_method, method_info, swagger_data=None):
    method_name = get_method_name(method_info)
    validate_type = get_validate_definition(method_info)
    uri_params = _get_uri_params(uri_path)
    request_params = method_info.get('parameters', [])[uri_path.count('{'):]
    request_body = getter('requestBody.content.application/json', method_info)
    request_body = [request_body] if request_body else []
    query_params, body_payload = _get_query_params_and_body(request_params + request_body)
    method_signature, query_params, body_payload = get_result_formatter_code(
        uri_params, query_params, body_payload, swagger_data
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
    from pprint import pprint
    import json
    # print(generate_interface(get_swagger_data('test'), 'lol'))
    datas = generate_type_schema({'type': 'object', 'properties': {'status': {'$ref': '#/definitions/Status'}, 'data': {'properties': {'assets': {'$ref': '#/components/schemas/RequestedAssetsInfo'},
                                                   'quotes': {'items': {'additionalProperties': {'pattern': '^\\d{1,}\\.?\\d+$',
                                                                                                 'type': 'string'},
                                                                        'properties': {'timestamp': {'type': 'string'}},
                                                                        'type': 'object'},
                                                              'type': 'array'}},
                                    'required': ['assets', 'quotes'],
                                    'type': 'object'}}}, 'types')
    pprint(datas)
    pprint(json.loads(str(datas)))
    # print(generate_interface('qwe'))
