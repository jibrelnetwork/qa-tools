import pathlib
from setuptools import find_packages, setup

version = pathlib.Path('version.txt').read_text().strip()

setup(
    name='qa_tool',
    description='Backend QA automation tools',
    version='0.1',
    packages=find_packages(),
)
