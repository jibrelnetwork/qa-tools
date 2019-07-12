import os
import json
import string
import requests
from qa_tool.utils.common import StatusCodes
from qa_tool.util_scripts.generate_api.generate_type import generate_types
from qa_tool.util_scripts.generate_api.generate_interface import generate_interface


unusable_symbols = string.punctuation + string.whitespace

apiDir = "./"
TYPE_IMPORTS = ["from qa_tool.utils.utils import classproperty"]
API_IMPORTS = ["from qa_tool.utils.api_helper import validate_type_wrap"]


def format_to_python_name(data):
    for sym in data:
        if sym in unusable_symbols:
            data = data.replace(sym, '')
    return data


def get_api_filepaths(service_name):
    service_name = service_name.lower()
    interface_filename = os.path.join(apiDir, service_name + ".py")
    types_filename = os.path.join(apiDir, 'types', service_name + "_types.py")
    return interface_filename, types_filename


def get_swagger_data(swagger_url):
    resp = requests.get(swagger_url)
    assert resp.status_code == StatusCodes.OK
    try:
        data = json.loads(resp.text)
    except Exception as e:
        data = resp.text
    return data


def save_data_with_imports(path_, data, imports):
    with open(path_, "w") as file_:
        data = '\n'.join(imports) + '\n'*2 + data
        file_.write(data)


def format_to_import(path_, as_statement):
    path_ = path_[:-3].split(os.sep)
    path_[0] = 'api'
    return 'import ' + '.'.join(path_) + f' as {as_statement}'


def generate_api(swagger_url, service_name=None):
    """
    :param swagger_url:
    :param service_name: default - title from swagger json
    """
    swagger_data = get_swagger_data(swagger_url)
    service_name = format_to_python_name(service_name or swagger_data['info']['title'])
    api_path, type_path = get_api_filepaths(service_name)
    api_str = generate_interface(swagger_data, service_name)
    types_str = generate_types(swagger_data)
    data_for_save = (
        (api_path, api_str, [format_to_import(type_path, 'types')] + API_IMPORTS),
        (type_path, types_str, TYPE_IMPORTS)
    )
    for path_, data, imports in data_for_save:
        save_data_with_imports(path_, data, imports)


if __name__ == "__main__":
    generate_api('http://127.0.0.1:8000/api/doc/swagger.json')
