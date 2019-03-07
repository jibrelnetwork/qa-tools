import os
import logging
import pytest
from JibrelTests.tests.JSearch.jsearch_specific import JsearchApiWrapper, ReferenceDataProvider, Validator


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@pytest.fixture(scope='session', autouse=True)
def setup():
    reference = ReferenceDataProvider(os.environ['NODE_URL'])
    jsearch = JsearchApiWrapper(os.environ['JSEARCH_URL'])
    validate = Validator()
    return jsearch, reference, validate
