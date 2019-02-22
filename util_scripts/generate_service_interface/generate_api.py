from util_scripts.generate_service_interface.generate_common import get_swagger_data, generate_api

CLASS_TEMPLATE = """
class {class_name}(object):
    def __init__(self, client):
        self.client = client
"""


METHOD_TEMPLATE = """
@validate_type_wrap(validate_type)
def {method_name}(method_signature):
    uri = f"{uri_path}"
    body = {body_payload}
    query_params = {query_params}
    return self.client.{request_method}(uri, body, query_params)
"""


def generate_interface(swagger_url):
    swagger_data = get_swagger_data(swagger_url)
    print(swagger_data)


if __name__ == "__main__":
    from test_json_validate import test_call
    generate_api('test')
    data, code = test_call()
