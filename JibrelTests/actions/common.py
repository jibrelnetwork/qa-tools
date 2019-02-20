

class ServiceCodes(object):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404
    SERVICE_ERROR = 500


class Methods(object):
    DELETE = "DELETE"
    GET = "GET"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"



"""
how we can validate data by external framework
1) https://pypi.org/project/flask-expects-json/
2) https://python-jsonschema.readthedocs.io/en/latest/validate/
3) https://marshmallow.readthedocs.io/en/latest/
4) https://richardtier.com/2014/03/24/json-schema-validation-with-django-rest-framework/
"""


