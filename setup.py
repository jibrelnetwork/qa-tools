import os
import pathlib
from setuptools import find_packages, setup


qa_tools_repo = pathlib.Path(__file__)/'..'
version = (qa_tools_repo/'version.txt').resolve().read_text().strip()


def get_requires():
    with (qa_tools_repo/'requirements.txt').resolve().open() as f:
        required = f.read().splitlines()
    return required


setup(
    name='qa_tool',
    description='Backend QA automation tools',
    version=version,
    include_package_data=True,
    packages=find_packages(),
    install_requires=get_requires(),
)
