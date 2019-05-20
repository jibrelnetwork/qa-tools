import re
from util_scripts.generate_api.generate_type import generate_type_schema, JsonFields, JsonTypes, get_def_name_from_ref

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
            if param['schema']['type'] == JsonTypes.ARRAY:
                if not isinstance(body, dict):
                    raise Exception("Can't detect body payload for method")
                items = param['schema']['items']
                if JsonFields.REF in items:
                    body = get_def_name_from_ref(items[JsonFields.REF]) + 's'
                elif JsonFields.TYPE in items:
                    body = items[JsonFields.TYPE] + '_array'
                body = body.lower()
                continue
            body['obj_field_name'] = 'obj_field_name'  # TODO: need implement when will add in swagger
    query = [delete_required_type(i) for i in query]
    return query, body


def _get_uri_params(uri_path):
    return re.findall(r'\{([\w]+)\}', uri_path)


def get_name_by_summary(summary_info):  # TODO: remove after Aleksey Selikhov fixes
    summary = summary_info['summary'].split(' ')
    summary = [i.capitalize() for i in summary]
    return ''.join(summary)


def get_method_name(method_info):
    return method_info.get('operationId', get_name_by_summary(method_info)).replace('.', '')


def get_validate_definition(method_info):
    responses = method_info['responses']
    for service_code, code_info in responses.items():
        if not service_code.startswith('2'):
            continue
        return generate_type_schema(code_info.get('schema', code_info), 'types')
    else:
        raise Exception("Can't detect 2XX service code")


def delete_required_type(param):
    for suff in REQUIRED_SUFFIX_TYPES:
        if suff in param:
            return param.replace(suff, '')
    return param


def get_stingify_params(params):
    if params:
        butter = "{%s\n        }"
        template = '\n' + ' ' * 12 + '"%s": %s,'
        code = [template % (k, k) for k in params]
        return butter % ("".join(code))
    else:
        return "{}"


def get_stringify_payload(params):
    if isinstance(params, str):
        result = params
    elif isinstance(params, dict):
        result = get_stingify_params(params)
    return result


def get_result_formatter_code(uri_params, query_params, body_payload):
    body_signature = [body_payload] if isinstance(body_payload, str) else [i for i in body_payload]
    signature = uri_params + query_params + body_signature
    query_params = get_stingify_params(query_params)
    body_payload = get_stringify_payload(body_payload)
    return ', '.join(signature), query_params, body_payload


def get_method_code(uri_path, request_method, method_info):
    method_name = get_method_name(method_info)
    validate_type = get_validate_definition(method_info)
    uri_params = _get_uri_params(uri_path)
    query_params, body_payload = _get_query_params_and_body(method_info.get('parameters', [])[uri_path.count('{'):])
    method_signature, query_params, body_payload = get_result_formatter_code(uri_params, query_params, body_payload)
    return METHOD_TEMPLATE.format(**locals())


def generate_interface(swagger_data, interface_name):
    result = [CLASS_TEMPLATE.format(interface_name=interface_name)]
    all_paths = swagger_data['paths']
    for uri_path, methods in all_paths.items():
        for request_method, method_info in methods.items():
            result.append(get_method_code(uri_path, request_method, method_info))
    return '\n'.join(result)


if __name__ == "__main__":
    from util_scripts.generate_api.generate_common import get_swagger_data
    print(generate_interface(get_swagger_data('test'), 'lol'))
    print(generate_type_schema({'type': 'object', 'properties': {'status': {'$ref': '#/definitions/Status'}, 'data': {'$ref': '#/definitions/Uncle'}}}))
    # print(generate_interface('qwe'))
