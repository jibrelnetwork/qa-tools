import json
import os
import string
from util_scripts.generate_service_interface.generate_type import generate_types

from JibrelTests.consts.project_paths import apiDir

unusable_symbols = string.punctuation + string.whitespace

API_IMPORTS = ["from api.helper import validate_type_wrap"]
TYPE_IMPORTS = ["from JibrelTests.utils.utils import classproperty"]



def format_to_python_name(data):
    for sym in data:
        if sym in unusable_symbols:
            data = data.replace(sym, '_')
    return data.lower()


def get_api_filepaths(service_name):
    interface_filename = os.path.join(apiDir, service_name + ".py")
    types_filename = os.path.join(apiDir, 'types', service_name + "_types.py")
    return interface_filename, types_filename


def get_swagger_data(swagger_url):
    with open('test.json') as file_:
        return json.load(file_)


def save_data(path_, data):
    with open(path_, "r+") as file_:
        file_.write(data)


def generate_api(swagger_url, service_name=None):
    """
    :param swagger_url:
    :param service_name: default - title from swagger json
    """
    swagger_data = get_swagger_data(swagger_url)
    service_name = format_to_python_name(service_name or swagger_data['info']['title'])
    api_path, type_path = get_api_filepaths(service_name)
    types_str = generate_types(swagger_data)


if __name__ == "__main__":
    generate_api('test')

