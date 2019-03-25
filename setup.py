import pathlib
from setuptools import find_packages, setup

version = pathlib.Path('version.txt').read_text().strip()


def get_requires():
    with open('requirements.txt') as f:
        required = f.read().splitlines()
    return required


setup(
    name='qa_tool',
    description='Backend QA automation tools',
    version='0.1',
    include_package_data=True,
    packages=find_packages(),
    install_requires=get_requires(),
)
